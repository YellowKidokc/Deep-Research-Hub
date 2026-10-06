//! Process runner: starts a program inside one apps\ folder, writes its
//! stdout+stderr to data\procs\<id>.log, and keeps a <id>.json record so the
//! page (and the hub after a restart) can show exactly what ran.

use std::collections::{BTreeMap, HashMap};
use std::path::{Component, Path, PathBuf};
use std::process::Stdio;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, bail, Context, Result};
use serde::{Deserialize, Serialize};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWriteExt};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;

/// One entry in hub\launch.json. Only these can be started from the page;
/// the HTTP edge never accepts a raw command line.
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Launch {
    pub id: String,
    pub label: String,
    /// Folder name under apps\.
    pub app: String,
    /// Working directory relative to apps\<app>.
    #[serde(default = "dot")]
    pub cwd: String,
    /// "python" resolves to the app's own interpreter; anything else is run as-is.
    pub program: String,
    /// May contain {data} (the hub's data folder) and {<param>} placeholders.
    #[serde(default)]
    pub args: Vec<String>,
    /// Values the page supplies at run time. Each is checked against its kind
    /// before it reaches an argument list.
    #[serde(default)]
    pub params: Vec<Param>,
    /// Steps run after the main one, in order, into the same log. Their cwd
    /// is relative to the repo root; "python" means the system interpreter.
    #[serde(default)]
    pub then: Vec<ThenStep>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ThenStep {
    pub program: String,
    #[serde(default)]
    pub args: Vec<String>,
    #[serde(default = "dot")]
    pub cwd: String,
}

struct Step {
    program: PathBuf,
    args: Vec<String>,
    cwd: PathBuf,
}

impl Step {
    fn line(&self) -> Vec<String> {
        let mut v = vec![self.program.display().to_string()];
        v.extend(self.args.iter().cloned());
        v
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Param {
    pub name: String,
    #[serde(default)]
    pub label: String,
    /// youtube_url | count
    pub kind: String,
    /// An empty optional param drops every argument that mentions it.
    #[serde(default)]
    pub optional: bool,
}

impl Launch {
    /// The main argument list with {data}, {started} and every {param} filled in.
    pub fn build_args(&self, data_dir: &Path, values: &BTreeMap<String, String>, started: u64) -> Result<Vec<String>> {
        self.fill(&self.args, data_dir, values, started)
    }

    pub fn fill(&self, args: &[String], data_dir: &Path, values: &BTreeMap<String, String>, started: u64) -> Result<Vec<String>> {
        let mut filled: BTreeMap<String, String> = BTreeMap::new();
        for p in &self.params {
            let v = values.get(&p.name).map(|s| s.trim()).unwrap_or("");
            if v.is_empty() {
                if !p.optional {
                    bail!("{} is required", p.name);
                }
                continue;
            }
            check_param(&p.kind, v).with_context(|| format!("bad {}", p.name))?;
            filled.insert(p.name.clone(), v.to_string());
        }
        let data = data_dir.display().to_string();
        let mut out = vec![];
        'arg: for a in args {
            let mut a = a.replace("{data}", &data).replace("{started}", &started.to_string());
            for p in &self.params {
                let tag = format!("{{{}}}", p.name);
                if a.contains(&tag) {
                    match filled.get(&p.name) {
                        Some(v) => a = a.replace(&tag, v),
                        None => continue 'arg,
                    }
                }
            }
            out.push(a);
        }
        Ok(out)
    }
}

fn check_param(kind: &str, v: &str) -> Result<()> {
    match kind {
        "youtube_url" => {
            const OK: [&str; 4] = [
                "https://www.youtube.com/",
                "https://youtube.com/",
                "https://m.youtube.com/",
                "https://youtu.be/",
            ];
            if v.len() > 500 || v.chars().any(char::is_whitespace) || !OK.iter().any(|p| v.starts_with(p)) {
                bail!("expected a https://www.youtube.com/... or https://youtu.be/... link");
            }
        }
        "count" => {
            if v.len() > 6 || !v.chars().all(|c| c.is_ascii_digit()) {
                bail!("expected a whole number");
            }
        }
        other => bail!("unknown param kind {other}"),
    }
    Ok(())
}

fn dot() -> String {
    ".".into()
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ProcRecord {
    pub id: u64,
    pub launch_id: String,
    pub label: String,
    pub app: String,
    pub cwd: String,
    pub cmd: Vec<String>,
    /// Follow-up steps, as run.
    #[serde(default)]
    pub then: Vec<Vec<String>>,
    #[serde(default)]
    pub params: BTreeMap<String, String>,
    /// Unix seconds.
    pub started: u64,
    pub ended: Option<u64>,
    /// running | exited | failed | stopped | lost
    pub status: String,
    pub exit_code: Option<i32>,
}

pub struct Procs {
    root: PathBuf,
    dir: PathBuf,
    records: Mutex<HashMap<u64, ProcRecord>>,
    children: Mutex<HashMap<u64, Child>>,
    next_id: Mutex<u64>,
}

pub fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

impl Procs {
    /// Loads earlier records from data\procs. Anything still marked running
    /// belonged to a previous hub process and is marked lost.
    pub fn load(root: &Path) -> Result<Arc<Self>> {
        let dir = root.join("data").join("procs");
        std::fs::create_dir_all(&dir).with_context(|| format!("create {}", dir.display()))?;
        let mut records = HashMap::new();
        let mut max_id = 0;
        for entry in std::fs::read_dir(&dir)? {
            let path = entry?.path();
            if path.extension().and_then(|e| e.to_str()) != Some("json") {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(&path) else { continue };
            let Ok(mut rec) = serde_json::from_str::<ProcRecord>(&text) else { continue };
            if rec.status == "running" {
                rec.status = "lost".into();
                std::fs::write(&path, serde_json::to_vec_pretty(&rec)?)?;
            }
            max_id = max_id.max(rec.id);
            records.insert(rec.id, rec);
        }
        Ok(Arc::new(Self {
            root: root.to_path_buf(),
            dir,
            records: Mutex::new(records),
            children: Mutex::new(HashMap::new()),
            next_id: Mutex::new(max_id + 1),
        }))
    }

    pub fn log_path(&self, id: u64) -> PathBuf {
        self.dir.join(format!("{id}.log"))
    }

    async fn save(&self, rec: &ProcRecord) {
        let path = self.dir.join(format!("{}.json", rec.id));
        if let Ok(bytes) = serde_json::to_vec_pretty(rec) {
            let _ = tokio::fs::write(path, bytes).await;
        }
    }

    pub async fn list(&self) -> Vec<ProcRecord> {
        let mut v: Vec<_> = self.records.lock().await.values().cloned().collect();
        v.sort_by(|a, b| b.id.cmp(&a.id));
        v
    }

    pub async fn get(&self, id: u64) -> Option<ProcRecord> {
        self.records.lock().await.get(&id).cloned()
    }

    pub async fn start(self: &Arc<Self>, launch: &Launch, values: &BTreeMap<String, String>) -> Result<ProcRecord> {
        let app_dir = self.root.join("apps").join(&launch.app);
        if !app_dir.is_dir() {
            bail!("no such app folder: apps/{}", launch.app);
        }
        let cwd = inside(&app_dir, &launch.cwd)
            .with_context(|| format!("bad cwd {} for app {}", launch.cwd, launch.app))?;
        let started = now();
        let data_dir = self.root.join("data");
        let program = if launch.program == "python" {
            python_for(&app_dir, &cwd)
        } else {
            PathBuf::from(&launch.program)
        };
        let mut steps = vec![Step { program, args: launch.build_args(&data_dir, values, started)?, cwd: cwd.clone() }];
        for t in &launch.then {
            let tcwd = inside(&self.root, &t.cwd).with_context(|| format!("bad cwd {} in then-step", t.cwd))?;
            let program = if t.program == "python" { system_python() } else { PathBuf::from(&t.program) };
            steps.push(Step { program, args: launch.fill(&t.args, &data_dir, values, started)?, cwd: tcwd });
        }

        let id = {
            let mut n = self.next_id.lock().await;
            let id = *n;
            *n += 1;
            id
        };
        let log = Arc::new(Mutex::new(tokio::fs::File::create(self.log_path(id)).await?));
        let rec = ProcRecord {
            id,
            launch_id: launch.id.clone(),
            label: launch.label.clone(),
            app: launch.app.clone(),
            cwd: cwd.display().to_string(),
            cmd: steps[0].line(),
            then: steps[1..].iter().map(Step::line).collect(),
            params: values.clone(),
            started,
            ended: None,
            status: "running".into(),
            exit_code: None,
        };
        self.save(&rec).await;
        self.records.lock().await.insert(id, rec.clone());

        let me = self.clone();
        tokio::spawn(async move { me.run_steps(id, steps, log).await });
        Ok(rec)
    }

    /// Runs each step in turn into the same log. A then-step runs even when
    /// the step before it failed (a partial download still gets summarized);
    /// nothing more runs once the job is stopped.
    async fn run_steps(self: Arc<Self>, id: u64, steps: Vec<Step>, log: Arc<Mutex<tokio::fs::File>>) {
        let mut worst: Option<i32> = Some(0);
        let mut all_ok = true;
        let multi = steps.len() > 1;
        for (i, step) in steps.into_iter().enumerate() {
            if self.get(id).await.map(|r| r.status != "running").unwrap_or(true) {
                break;
            }
            if multi {
                let head = format!("\n[hub] step {}: {}\n", i + 1, step.line().join(" "));
                let _ = log.lock().await.write_all(head.as_bytes()).await;
            }
            let (ok, code) = self.run_one(id, &step, &log).await;
            if !ok {
                all_ok = false;
                if worst == Some(0) {
                    worst = code;
                }
            }
        }
        let mut records = self.records.lock().await;
        if let Some(rec) = records.get_mut(&id) {
            rec.ended = Some(now());
            rec.exit_code = worst;
            if rec.status == "running" {
                rec.status = if all_ok { "exited".into() } else { "failed".into() };
            }
            let rec = rec.clone();
            drop(records);
            self.save(&rec).await;
        }
    }

    async fn run_one(&self, id: u64, step: &Step, log: &Arc<Mutex<tokio::fs::File>>) -> (bool, Option<i32>) {
        let spawned = Command::new(&step.program)
            .args(&step.args)
            .current_dir(&step.cwd)
            .env("PYTHONUNBUFFERED", "1")
            .env("PYTHONIOENCODING", "utf-8")
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();
        let mut child = match spawned {
            Ok(c) => c,
            Err(e) => {
                let msg = format!("[hub] failed to start {}: {e}\n", step.program.display());
                let _ = log.lock().await.write_all(msg.as_bytes()).await;
                return (false, None);
            }
        };
        let (Some(out), Some(err)) = (child.stdout.take(), child.stderr.take()) else {
            return (false, None);
        };
        let pump_out = tokio::spawn(pump(out, log.clone()));
        let pump_err = tokio::spawn(pump(err, log.clone()));
        self.children.lock().await.insert(id, child);
        let _ = pump_out.await;
        let _ = pump_err.await;
        let child = self.children.lock().await.remove(&id);
        let status = match child {
            Some(mut c) => c.wait().await.ok(),
            None => None,
        };
        (status.map(|s| s.success()).unwrap_or(false), status.and_then(|s| s.code()))
    }

    pub async fn stop(&self, id: u64) -> Result<()> {
        let mut children = self.children.lock().await;
        let child = children.get_mut(&id).ok_or_else(|| anyhow!("process {id} is not running"))?;
        child.start_kill()?;
        drop(children);
        if let Some(rec) = self.records.lock().await.get_mut(&id) {
            rec.status = "stopped".into();
        }
        Ok(())
    }
}

async fn pump<R: AsyncRead + Unpin>(mut r: R, log: Arc<Mutex<tokio::fs::File>>) {
    let mut buf = [0u8; 8192];
    loop {
        match r.read(&mut buf).await {
            Ok(0) | Err(_) => break,
            Ok(n) => {
                let mut f = log.lock().await;
                let _ = f.write_all(&buf[..n]).await;
                let _ = f.flush().await;
            }
        }
    }
}

/// `base` joined with plain folder names only: "." is dropped; "..", roots
/// and drive prefixes are refused, so the result stays inside `base`.
fn inside(base: &Path, rel: &str) -> Result<PathBuf> {
    let mut p = base.to_path_buf();
    for part in Path::new(rel).components() {
        match part {
            Component::Normal(x) => p.push(x),
            Component::CurDir => {}
            _ => bail!("must stay inside {}", base.display()),
        }
    }
    if !p.is_dir() {
        bail!("{} is not a folder", p.display());
    }
    Ok(p)
}

fn system_python() -> PathBuf {
    PathBuf::from(if cfg!(windows) { "python" } else { "python3" })
}

/// The app's own interpreter: a .venv or venv between the working directory
/// and the app root, else the system Python. Nothing is shared between apps.
fn python_for(app_dir: &Path, cwd: &Path) -> PathBuf {
    let (sub, exe) = if cfg!(windows) {
        ("Scripts", "python.exe")
    } else {
        ("bin", "python")
    };
    let mut dir = Some(cwd);
    while let Some(d) = dir {
        for venv in [".venv", "venv"] {
            let p = d.join(venv).join(sub).join(exe);
            if p.is_file() {
                return p;
            }
        }
        if d == app_dir {
            break;
        }
        dir = d.parent();
    }
    system_python()
}
