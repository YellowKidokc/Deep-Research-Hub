//! Process runner: starts a program inside one apps\ folder, writes its
//! stdout+stderr to data\procs\<id>.log, and keeps a <id>.json record so the
//! page (and the hub after a restart) can show exactly what ran.

use std::collections::HashMap;
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
    #[serde(default)]
    pub args: Vec<String>,
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

    pub async fn start(self: &Arc<Self>, launch: &Launch) -> Result<ProcRecord> {
        let app_dir = self.root.join("apps").join(&launch.app);
        if !app_dir.is_dir() {
            bail!("no such app folder: apps/{}", launch.app);
        }
        // Plain folder names only: "." is dropped, "..", roots and drive
        // prefixes are refused, so the working directory stays inside the app.
        let mut cwd = app_dir.clone();
        for part in Path::new(&launch.cwd).components() {
            match part {
                Component::Normal(p) => cwd.push(p),
                Component::CurDir => {}
                _ => bail!("bad cwd {} for app {}: must stay inside the app folder", launch.cwd, launch.app),
            }
        }
        if !cwd.is_dir() {
            bail!("bad cwd {} for app {}: not a folder", launch.cwd, launch.app);
        }
        let program = if launch.program == "python" {
            python_for(&app_dir, &cwd)
        } else {
            PathBuf::from(&launch.program)
        };

        let id = {
            let mut n = self.next_id.lock().await;
            let id = *n;
            *n += 1;
            id
        };
        let mut cmd_line = vec![program.display().to_string()];
        cmd_line.extend(launch.args.iter().cloned());

        let log = tokio::fs::File::create(self.log_path(id)).await?;
        let log = Arc::new(Mutex::new(log));

        let mut rec = ProcRecord {
            id,
            launch_id: launch.id.clone(),
            label: launch.label.clone(),
            app: launch.app.clone(),
            cwd: cwd.display().to_string(),
            cmd: cmd_line,
            started: now(),
            ended: None,
            status: "running".into(),
            exit_code: None,
        };

        let spawned = Command::new(&program)
            .args(&launch.args)
            .current_dir(&cwd)
            .env("PYTHONUNBUFFERED", "1")
            .env("PYTHONIOENCODING", "utf-8")
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn();

        let mut child = match spawned {
            Ok(c) => c,
            Err(e) => {
                let msg = format!("[hub] failed to start {}: {e}\n", program.display());
                log.lock().await.write_all(msg.as_bytes()).await?;
                rec.status = "failed".into();
                rec.ended = Some(now());
                self.save(&rec).await;
                self.records.lock().await.insert(id, rec.clone());
                return Ok(rec);
            }
        };

        let out = child.stdout.take().ok_or_else(|| anyhow!("no stdout"))?;
        let err = child.stderr.take().ok_or_else(|| anyhow!("no stderr"))?;
        let pump_out = tokio::spawn(pump(out, log.clone()));
        let pump_err = tokio::spawn(pump(err, log.clone()));

        self.save(&rec).await;
        self.records.lock().await.insert(id, rec.clone());
        self.children.lock().await.insert(id, child);

        let me = self.clone();
        tokio::spawn(async move {
            let _ = pump_out.await;
            let _ = pump_err.await;
            me.reap(id).await;
        });

        Ok(rec)
    }

    /// Called once both output pipes close. Waits for the exit status and
    /// writes the final record.
    async fn reap(&self, id: u64) {
        let child = self.children.lock().await.remove(&id);
        let status = match child {
            Some(mut c) => c.wait().await.ok(),
            None => None,
        };
        let mut records = self.records.lock().await;
        if let Some(rec) = records.get_mut(&id) {
            rec.ended = Some(now());
            rec.exit_code = status.and_then(|s| s.code());
            if rec.status == "running" {
                rec.status = match status {
                    Some(s) if s.success() => "exited".into(),
                    _ => "failed".into(),
                };
            }
            let rec = rec.clone();
            drop(records);
            self.save(&rec).await;
        }
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
    PathBuf::from(if cfg!(windows) { "python" } else { "python3" })
}
