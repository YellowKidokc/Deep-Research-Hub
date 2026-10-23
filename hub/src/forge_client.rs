//! forge_client: the hub's only road to an AI model.
//!
//! Forge (repo Rust_AI_API) is the one service that holds provider keys and
//! SDKs. The hub holds none: every AI call from every screen goes through
//! `call` to Forge's local port, and there is no fallback to a direct call.
//! If Forge is down the call fails loudly with a 503 that says so.
//!
//! FORGE_URL sets where Forge lives (default http://127.0.0.1:8790).
//! The retry policy lives here and nowhere else.

use std::sync::Arc;
use std::time::Duration;

use anyhow::{anyhow, bail, Result};
use serde::Serialize;
use tokio::sync::watch;

use crate::http1::{self, Failure, Reply};
use crate::procs::now;

pub const DEFAULT_URL: &str = "http://127.0.0.1:8790";

/// Retry policy, the only one: a call whose connection was refused (so
/// nothing reached Forge) is tried again after each of these pauses. A call
/// that reached Forge is never repeated, because it may have cost money.
const RETRY_PAUSES_MS: [u64; 2] = [250, 1000];
/// How long one AI call may take before the hub gives up on it.
const CALL_TIMEOUT: Duration = Duration::from_secs(600);
const HEALTH_EVERY: Duration = Duration::from_secs(5);
const HEALTH_TIMEOUT: Duration = Duration::from_secs(3);

#[derive(Clone, Debug, Serialize, PartialEq)]
pub struct ForgeState {
    pub url: String,
    /// None until the first health check finishes.
    pub up: Option<bool>,
    /// Unix seconds of the last check.
    pub checked: u64,
    /// Why the last check failed.
    pub error: Option<String>,
}

pub struct Forge {
    url: String,
    host: String,
    port: u16,
    /// Path prefix from FORGE_URL, without a trailing slash ("" for none).
    prefix: String,
    state: watch::Sender<ForgeState>,
}

impl Forge {
    pub fn from_env() -> Result<Arc<Self>> {
        let url = std::env::var("FORGE_URL").unwrap_or_else(|_| DEFAULT_URL.into());
        let url = url.trim_end_matches('/').to_string();
        let Some(rest) = url.strip_prefix("http://") else {
            bail!("FORGE_URL must be a local http:// address, got {url}");
        };
        let (authority, prefix) = match rest.find('/') {
            Some(i) => (&rest[..i], rest[i..].to_string()),
            None => (rest, String::new()),
        };
        let (host, port) = match authority.rsplit_once(':') {
            Some((h, p)) => (h.to_string(), p.parse().map_err(|_| anyhow!("bad port in FORGE_URL {url}"))?),
            None => (authority.to_string(), 80),
        };
        let (state, _) = watch::channel(ForgeState { url: url.clone(), up: None, checked: 0, error: None });
        Ok(Arc::new(Self { url, host, port, prefix, state }))
    }

    pub fn state(&self) -> ForgeState {
        self.state.borrow().clone()
    }

    /// Fires on every change of up/down (not on every check).
    pub fn subscribe(&self) -> watch::Receiver<ForgeState> {
        self.state.subscribe()
    }

    /// Checks Forge on hub start and every few seconds after. Any HTTP answer
    /// at all counts as up; only a refused or silent port counts as down.
    pub async fn watch_health(self: Arc<Self>) {
        loop {
            let path = if self.prefix.is_empty() { "/".to_string() } else { format!("{}/", self.prefix) };
            let result = http1::request(&self.host, self.port, "GET", &path, None, &[], HEALTH_TIMEOUT).await;
            let error = match result {
                Ok(_) => None,
                Err(Failure::Connect(e) | Failure::Other(e)) => Some(format!("{e:#}")),
            };
            let up = error.is_none();
            let was = self.state.borrow().up;
            if was != Some(up) {
                match &error {
                    None => println!("[forge] up at {}", self.url),
                    Some(e) => eprintln!("[forge] DOWN at {}: {e}", self.url),
                }
            }
            self.state.send_if_modified(|s| {
                let changed = s.up != Some(up);
                s.up = Some(up);
                s.checked = now();
                s.error = error.clone();
                changed
            });
            tokio::time::sleep(HEALTH_EVERY).await;
        }
    }

    /// One AI call, passed through to Forge as is. `path_and_query` is the
    /// part after FORGE_URL, starting with "/".
    pub async fn call(&self, method: &str, path_and_query: &str, content_type: Option<&str>, body: &[u8]) -> Result<Reply> {
        let path = format!("{}{}", self.prefix, path_and_query);
        let mut attempt = 0;
        loop {
            match http1::request(&self.host, self.port, method, &path, content_type, body, CALL_TIMEOUT).await {
                Ok(reply) => return Ok(reply),
                Err(Failure::Connect(_)) if attempt < RETRY_PAUSES_MS.len() => {
                    tokio::time::sleep(Duration::from_millis(RETRY_PAUSES_MS[attempt])).await;
                    attempt += 1;
                }
                Err(Failure::Connect(e)) => {
                    self.mark_down(&e);
                    bail!("Forge is down at {} ({e:#}). Start Forge and try again; the hub never calls a model directly.", self.url)
                }
                Err(Failure::Other(e)) => bail!("Forge call {method} {path_and_query} failed: {e:#}"),
            }
        }
    }

    /// A call just found Forge gone; don't wait for the next health check
    /// to tell the tray.
    fn mark_down(&self, e: &anyhow::Error) {
        self.state.send_if_modified(|s| {
            let changed = s.up != Some(false);
            s.up = Some(false);
            s.checked = now();
            s.error = Some(format!("{e:#}"));
            changed
        });
    }
}
