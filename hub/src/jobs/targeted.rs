//! Screen 2: Targeted Research. The battery definition
//! (prompts\T_targeted\battery.json) and the runs drh_targeted.py writes to
//! data\targeted\<topic-slug>\<stamp>\.

use std::path::PathBuf;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Deserialize;
use serde_json::{json, Value};

use crate::Hub;

const RUN_FILES: [&str; 4] = ["facts.md", "facts.json", "run.json", "error.txt"];

fn runs_dir(hub: &Hub) -> PathBuf {
    hub.root.join("data").join("targeted")
}

pub async fn battery(State(hub): State<Hub>) -> Response {
    let p = hub.root.join("prompts").join("T_targeted").join("battery.json");
    match tokio::fs::read_to_string(&p).await {
        Ok(text) => match serde_json::from_str::<Value>(text.trim_start_matches('\u{feff}')) {
            Ok(v) => Json(v).into_response(),
            Err(e) => (StatusCode::INTERNAL_SERVER_ERROR, Json(json!({ "error": format!("{}: {e}", p.display()) }))).into_response(),
        },
        Err(e) => (StatusCode::NOT_FOUND, Json(json!({ "error": format!("{}: {e}", p.display()) }))).into_response(),
    }
}

pub async fn runs(State(hub): State<Hub>) -> Response {
    let base = runs_dir(&hub);
    let res = tokio::task::spawn_blocking(move || {
        let mut out = vec![];
        for topic in std::fs::read_dir(&base).into_iter().flatten().flatten() {
            if !topic.path().is_dir() {
                continue;
            }
            for run in std::fs::read_dir(topic.path()).into_iter().flatten().flatten() {
                if !run.path().is_dir() {
                    continue;
                }
                let rec: Value = std::fs::read_to_string(run.path().join("run.json"))
                    .ok()
                    .and_then(|t| serde_json::from_str(&t).ok())
                    .unwrap_or(Value::Null);
                let failed_early = run.path().join("error.txt").is_file() && rec.is_null();
                out.push(json!({
                    "topic_dir": topic.file_name().to_string_lossy(),
                    "stamp": run.file_name().to_string_lossy(),
                    "topic": rec.get("topic").cloned().unwrap_or(Value::Null),
                    "status": if failed_early { json!("failed") } else { rec.get("status").cloned().unwrap_or(json!("running")) },
                    "summary": rec.get("summary").cloned().unwrap_or(Value::Null),
                    "findings": rec.get("findings").cloned().unwrap_or(Value::Null),
                    "rejected": rec.get("rejected").cloned().unwrap_or(Value::Null),
                    "seconds": rec.get("seconds").cloned().unwrap_or(Value::Null),
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
    topic_dir: String,
    stamp: String,
    name: String,
}

fn plain(s: &str) -> bool {
    !s.is_empty() && s != "." && s != ".." && !s.contains(['/', '\\', ':'])
}

pub async fn file(State(hub): State<Hub>, Query(q): Query<FileQuery>) -> Response {
    if !plain(&q.topic_dir) || !plain(&q.stamp) || !RUN_FILES.contains(&q.name.as_str()) {
        return (StatusCode::BAD_REQUEST, Json(json!({ "error": "bad file request" }))).into_response();
    }
    let p = runs_dir(&hub).join(&q.topic_dir).join(&q.stamp).join(&q.name);
    match tokio::fs::read_to_string(&p).await {
        Ok(text) => Json(json!({ "path": p.display().to_string(), "text": text })).into_response(),
        Err(e) => (StatusCode::NOT_FOUND, Json(json!({ "error": e.to_string() }))).into_response(),
    }
}
