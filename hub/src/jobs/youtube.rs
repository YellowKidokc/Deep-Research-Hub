//! Screen 5: the transcript library ytgrab.py writes into data\youtube\<Channel>\.

use std::path::{Path, PathBuf};

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::Hub;

/// Folders ytgrab's cleaner and the archiver create; not channels or videos.
const SKIP: [&str; 4] = ["Clean MD", "Channel Summary", "Prompts", "_archive"];
const SUMMARY: &str = "\n## Baseline Summary";
const FAILED: &str = "**Retrieved via:** failed";
const NONE: &str = "**Retrieved via:** no_transcript";

#[derive(Serialize)]
struct Video {
    name: String,
    bytes: u64,
    modified: u64,
    /// ok | failed | no_transcript
    state: &'static str,
    summarized: bool,
}

#[derive(Serialize)]
struct Channel {
    name: String,
    videos: Vec<Video>,
}

fn root(hub: &Hub) -> PathBuf {
    hub.root.join("data").join("youtube")
}

fn modified(p: &Path) -> u64 {
    p.metadata()
        .and_then(|m| m.modified())
        .ok()
        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

pub async fn library(State(hub): State<Hub>) -> Response {
    let base = root(&hub);
    let res = tokio::task::spawn_blocking(move || {
        let mut channels = vec![];
        let Ok(rd) = std::fs::read_dir(&base) else { return channels };
        for ch in rd.flatten() {
            let name = ch.file_name().to_string_lossy().to_string();
            if !ch.path().is_dir() || SKIP.contains(&name.as_str()) {
                continue;
            }
            let mut videos = vec![];
            for f in std::fs::read_dir(ch.path()).into_iter().flatten().flatten() {
                let p = f.path();
                if p.extension().and_then(|e| e.to_str()) != Some("md") || !p.is_file() {
                    continue;
                }
                let text = std::fs::read_to_string(&p).unwrap_or_default();
                let state = if text.contains(FAILED) {
                    "failed"
                } else if text.contains(NONE) {
                    "no_transcript"
                } else {
                    "ok"
                };
                videos.push(Video {
                    name: f.file_name().to_string_lossy().to_string(),
                    bytes: text.len() as u64,
                    modified: modified(&p),
                    state,
                    summarized: text.contains(SUMMARY),
                });
            }
            videos.sort_by(|a, b| b.modified.cmp(&a.modified));
            channels.push(Channel { name, videos });
        }
        channels.sort_by(|a, b| a.name.to_lowercase().cmp(&b.name.to_lowercase()));
        channels
    })
    .await
    .unwrap_or_default();
    Json(json!({ "root": root(&hub).display().to_string(), "channels": res })).into_response()
}

#[derive(Deserialize)]
pub struct FileQuery {
    channel: String,
    name: String,
}

/// One name, no separators, no "..": the file must sit directly in a channel folder.
fn plain(s: &str) -> bool {
    !s.is_empty() && s != "." && s != ".." && !s.contains(['/', '\\', ':'])
}

pub async fn file(State(hub): State<Hub>, Query(q): Query<FileQuery>) -> Response {
    if !plain(&q.channel) || !plain(&q.name) || !q.name.ends_with(".md") {
        return (StatusCode::BAD_REQUEST, Json(json!({ "error": "bad file name" }))).into_response();
    }
    let p = root(&hub).join(&q.channel).join(&q.name);
    match tokio::fs::read_to_string(&p).await {
        Ok(text) => Json(json!({ "path": p.display().to_string(), "text": text })).into_response(),
        Err(e) => (StatusCode::NOT_FOUND, Json(json!({ "error": e.to_string() }))).into_response(),
    }
}
