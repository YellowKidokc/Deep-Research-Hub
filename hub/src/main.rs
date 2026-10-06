//! Deep Research Hub — the wrapper.
//!
//! Owns only the boring parts: starting and stopping the apps under apps\,
//! serving web\dist, and logging. No research logic lives here.
//!
//! Run from the repo root (or set DRH_ROOT):  cargo run --manifest-path hub/Cargo.toml
//! Then open http://127.0.0.1:2828  (DRH_PORT to change).

mod jobs;
mod procs;

use std::collections::BTreeMap;
use std::net::SocketAddr;
use std::path::{Component, Path, PathBuf};
use std::sync::Arc;

use anyhow::{Context, Result};
use axum::{
    body::Bytes,
    extract::{Path as UrlPath, Query, State},
    http::{header, StatusCode, Uri},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::Deserialize;
use serde_json::json;

use procs::{Launch, Procs};

#[derive(Clone)]
pub struct Hub {
    pub root: PathBuf,
    procs: Arc<Procs>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let root = find_root()?;
    let procs = Procs::load(&root)?;
    let hub = Hub { root: root.clone(), procs };

    let app = Router::new()
        .route("/api/health", get(|| async { Json(json!({ "ok": true })) }))
        .route("/api/apps", get(list_apps))
        .route("/api/launch", get(list_launch))
        .route("/api/launch/{id}", post(start_launch))
        .route("/api/procs", get(list_procs))
        .route("/api/procs/{id}", get(get_proc))
        .route("/api/procs/{id}/log", get(get_log))
        .route("/api/procs/{id}/stop", post(stop_proc))
        .route("/api/youtube/library", get(jobs::youtube::library))
        .route("/api/youtube/file", get(jobs::youtube::file))
        .fallback(static_file)
        .with_state(hub);

    let port: u16 = std::env::var("DRH_PORT").ok().and_then(|p| p.parse().ok()).unwrap_or(2828);
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let listener = tokio::net::TcpListener::bind(addr).await.with_context(|| format!("bind {addr}"))?;
    println!("[hub] root {}", root.display());
    println!("[hub] serving http://{addr}");
    axum::serve(listener, app).await?;
    Ok(())
}

/// DRH_ROOT, else the nearest folder at or above the current one that holds
/// both apps\ and hub\.
fn find_root() -> Result<PathBuf> {
    if let Ok(r) = std::env::var("DRH_ROOT") {
        return Ok(PathBuf::from(r));
    }
    let mut dir = std::env::current_dir()?;
    loop {
        if dir.join("apps").is_dir() && dir.join("hub").is_dir() {
            return Ok(dir);
        }
        if !dir.pop() {
            anyhow::bail!("run from inside the deep-research-hub folder or set DRH_ROOT");
        }
    }
}

fn err(code: StatusCode, msg: impl ToString) -> Response {
    (code, Json(json!({ "error": msg.to_string() }))).into_response()
}

fn read_launch(root: &Path) -> Result<Vec<Launch>> {
    let path = root.join("hub").join("launch.json");
    let text = std::fs::read_to_string(&path).with_context(|| format!("read {}", path.display()))?;
    Ok(serde_json::from_str(&text).with_context(|| format!("parse {}", path.display()))?)
}

async fn list_apps(State(hub): State<Hub>) -> Response {
    let mut apps = vec![];
    if let Ok(rd) = std::fs::read_dir(hub.root.join("apps")) {
        for e in rd.flatten() {
            if e.path().is_dir() {
                let name = e.file_name().to_string_lossy().to_string();
                let upstream = std::fs::read(e.path().join("UPSTREAM.md"))
                    .map(|b| decode_text(&b).trim().to_string())
                    .unwrap_or_default();
                apps.push(json!({ "name": name, "upstream": upstream }));
            }
        }
    }
    apps.sort_by(|a, b| a["name"].as_str().cmp(&b["name"].as_str()));
    Json(apps).into_response()
}

async fn list_launch(State(hub): State<Hub>) -> Response {
    match read_launch(&hub.root) {
        Ok(l) => Json(l).into_response(),
        Err(e) => err(StatusCode::INTERNAL_SERVER_ERROR, format!("{e:#}")),
    }
}

#[derive(Deserialize, Default)]
struct StartBody {
    #[serde(default)]
    params: BTreeMap<String, String>,
}

/// Body is optional: {"params": {"url": "..."}} for entries that declare params.
async fn start_launch(State(hub): State<Hub>, UrlPath(id): UrlPath<String>, body: Bytes) -> Response {
    let body: StartBody = if body.is_empty() {
        StartBody::default()
    } else {
        match serde_json::from_slice(&body) {
            Ok(b) => b,
            Err(e) => return err(StatusCode::BAD_REQUEST, format!("bad body: {e}")),
        }
    };
    let launches = match read_launch(&hub.root) {
        Ok(l) => l,
        Err(e) => return err(StatusCode::INTERNAL_SERVER_ERROR, format!("{e:#}")),
    };
    let Some(launch) = launches.into_iter().find(|l| l.id == id) else {
        return err(StatusCode::NOT_FOUND, format!("no launch entry {id}"));
    };
    match hub.procs.start(&launch, &body.params).await {
        Ok(rec) => {
            println!("[hub] started #{} {} ({})", rec.id, rec.label, rec.status);
            Json(rec).into_response()
        }
        Err(e) => err(StatusCode::BAD_REQUEST, format!("{e:#}")),
    }
}

async fn list_procs(State(hub): State<Hub>) -> Response {
    Json(hub.procs.list().await).into_response()
}

async fn get_proc(State(hub): State<Hub>, UrlPath(id): UrlPath<u64>) -> Response {
    match hub.procs.get(id).await {
        Some(r) => Json(r).into_response(),
        None => err(StatusCode::NOT_FOUND, "no such process"),
    }
}

#[derive(Deserialize)]
struct LogQuery {
    #[serde(default)]
    from: u64,
}

/// Returns the log from byte offset `from`, plus the next offset to ask for.
/// The page polls this; a reload starts from 0 and shows everything again.
async fn get_log(State(hub): State<Hub>, UrlPath(id): UrlPath<u64>, Query(q): Query<LogQuery>) -> Response {
    let Some(rec) = hub.procs.get(id).await else {
        return err(StatusCode::NOT_FOUND, "no such process");
    };
    let bytes = tokio::fs::read(hub.procs.log_path(id)).await.unwrap_or_default();
    let from = (q.from as usize).min(bytes.len());
    let text = String::from_utf8_lossy(&bytes[from..]).to_string();
    Json(json!({ "text": text, "next": bytes.len(), "status": rec.status, "exit_code": rec.exit_code }))
        .into_response()
}

async fn stop_proc(State(hub): State<Hub>, UrlPath(id): UrlPath<u64>) -> Response {
    match hub.procs.stop(id).await {
        Ok(()) => Json(json!({ "ok": true })).into_response(),
        Err(e) => err(StatusCode::BAD_REQUEST, e),
    }
}

/// Serves web\dist. Unknown paths get index.html so the page can route.
async fn static_file(State(hub): State<Hub>, uri: Uri) -> Response {
    let dist = hub.root.join("web").join("dist");
    let rel = uri.path().trim_start_matches('/');
    if rel.starts_with("api/") {
        return err(StatusCode::NOT_FOUND, "no such endpoint");
    }
    let safe = Path::new(rel).components().all(|c| matches!(c, Component::Normal(_)));
    let mut path = if safe && !rel.is_empty() { dist.join(rel) } else { dist.join("index.html") };
    if !path.is_file() {
        path = dist.join("index.html");
    }
    match tokio::fs::read(&path).await {
        Ok(bytes) => ([(header::CONTENT_TYPE, mime(&path))], bytes).into_response(),
        Err(_) => (
            StatusCode::SERVICE_UNAVAILABLE,
            "web/dist not built. Run: cd web && npm install && npm run build",
        )
            .into_response(),
    }
}

fn mime(p: &Path) -> &'static str {
    match p.extension().and_then(|e| e.to_str()).unwrap_or("") {
        "html" => "text/html; charset=utf-8",
        "js" => "text/javascript; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "svg" => "image/svg+xml",
        "json" => "application/json",
        "png" => "image/png",
        "ico" => "image/x-icon",
        _ => "application/octet-stream",
    }
}

/// UPSTREAM.md files were written on Windows, some as UTF-16.
fn decode_text(b: &[u8]) -> String {
    if b.len() >= 2 && b[0] == 0xFF && b[1] == 0xFE {
        let units: Vec<u16> = b[2..].chunks_exact(2).map(|c| u16::from_le_bytes([c[0], c[1]])).collect();
        return String::from_utf16_lossy(&units);
    }
    let b = b.strip_prefix(&[0xEF, 0xBB, 0xBF]).unwrap_or(b);
    String::from_utf8_lossy(b).to_string()
}
