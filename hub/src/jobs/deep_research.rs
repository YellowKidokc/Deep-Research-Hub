//! Screen 1: the Deep Research queue (data\jobs\) and its runs
//! (data\deep_research\<job>\<stamp>\), written by drh_queue.py.

use std::path::{Path, PathBuf};

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Deserialize;
use serde_json::{json, Value};

use crate::Hub;

const RUN_FILES: [&str; 6] = ["report.md", "receipt.json", "sources.json", "run.json", "error.txt", "events.jsonl"];

fn jobs_dir(hub: &Hub) -> PathBuf {
    hub.root.join("data").join("jobs")
}

fn runs_dir(hub: &Hub) -> PathBuf {
    hub.root.join("data").join("deep_research")
}

/// The `query:` line of a job file, without a YAML parser.
fn query_of(p: &Path) -> String {
    let text = std::fs::read_to_string(p).unwrap_or_default();
    text.lines()
        .find_map(|l| l.strip_prefix("query:"))
        .map(|q| q.trim().trim_matches('"').trim_matches('\'').to_string())
        .unwrap_or_default()
}

fn yaml_files(dir: &Path) -> Vec<PathBuf> {
    let mut v: Vec<PathBuf> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().and_then(|e| e.to_str()) == Some("yaml"))
        .collect();
    v.sort();
    v
}

fn listing(dir: &Path, skip_defaults: bool) -> Vec<Value> {
    yaml_files(dir)
        .into_iter()
        .filter(|p| !(skip_defaults && p.file_name().and_then(|n| n.to_str()).is_some_and(|n| n.starts_with('_'))))
        .map(|p| json!({ "name": p.file_stem().unwrap_or_default().to_string_lossy(), "query": query_of(&p) }))
        .collect()
}

pub async fn jobs(State(hub): State<Hub>) -> Response {
    let dir = jobs_dir(&hub);
    let res = tokio::task::spawn_blocking(move || {
        json!({
            "dir": dir.display().to_string(),
            "has_defaults": dir.join("_defaults.yaml").is_file(),
            "pending": listing(&dir, true),
            "running": listing(&dir.join("running"), false),
            "done": listing(&dir.join("done"), false),
            "failed": listing(&dir.join("failed"), false),
        })
    })
    .await
    .unwrap_or_else(|_| json!({}));
    Json(res).into_response()
}

pub async fn runs(State(hub): State<Hub>) -> Response {
    let base = runs_dir(&hub);
    let res = tokio::task::spawn_blocking(move || {
        let mut out = vec![];
        for job in std::fs::read_dir(&base).into_iter().flatten().flatten() {
            let name = job.file_name().to_string_lossy().to_string();
            if name.starts_with('_') || !job.path().is_dir() {
                continue;
            }
            for run in std::fs::read_dir(job.path()).into_iter().flatten().flatten() {
                let rec: Value = std::fs::read_to_string(run.path().join("run.json"))
                    .ok()
                    .and_then(|t| serde_json::from_str(&t).ok())
                    .unwrap_or(Value::Null);
                out.push(json!({
                    "job": name,
                    "stamp": run.file_name().to_string_lossy(),
                    "status": rec.get("status").cloned().unwrap_or(json!("running")),
                    "query": rec.pointer("/job/query").cloned().unwrap_or(Value::Null),
                    "model": rec.get("model").cloned().unwrap_or(Value::Null),
                    "seconds": rec.get("seconds").cloned().unwrap_or(Value::Null),
                    "error": rec.get("error").cloned().unwrap_or(Value::Null),
                    "receipt": rec.get("receipt_summary").cloned().unwrap_or(Value::Null),
                }));
            }
        }
        out.sort_by(|a, b| b["stamp"].as_str().cmp(&a["stamp"].as_str()));
        out
    })
    .await
    .unwrap_or_default();
    Json(json!({ "dir": runs_dir(&hub).display().to_string(), "runs": res })).into_response()
}

#[derive(Deserialize)]
pub struct FileQuery {
    job: String,
    stamp: String,
    name: String,
}

fn plain(s: &str) -> bool {
    !s.is_empty() && s != "." && s != ".." && !s.contains(['/', '\\', ':'])
}

pub async fn file(State(hub): State<Hub>, Query(q): Query<FileQuery>) -> Response {
    if !plain(&q.job) || !plain(&q.stamp) || !RUN_FILES.contains(&q.name.as_str()) {
        return (StatusCode::BAD_REQUEST, Json(json!({ "error": "bad file request" }))).into_response();
    }
    let p = runs_dir(&hub).join(&q.job).join(&q.stamp).join(&q.name);
    match tokio::fs::read_to_string(&p).await {
        Ok(text) => Json(json!({ "path": p.display().to_string(), "text": text })).into_response(),
        Err(e) => (StatusCode::NOT_FOUND, Json(json!({ "error": e.to_string() }))).into_response(),
    }
}
