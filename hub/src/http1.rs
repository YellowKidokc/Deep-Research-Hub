//! The smallest HTTP client that does the job: one HTTP/1.0 request over a
//! plain TCP socket, read to end of stream. Only ever talks to 127.0.0.1
//! (Forge, or another copy of this hub), so no TLS and no new crate.
//! HTTP/1.0 means the server may not answer chunked; the body ends at EOF.

use std::time::Duration;

use anyhow::{anyhow, bail, Context, Result};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

pub struct Reply {
    pub status: u16,
    pub content_type: Option<String>,
    pub body: Vec<u8>,
}

/// Why a request failed. `Connect` means nothing was sent, so it is always
/// safe to try again; anything later might have reached the server.
pub enum Failure {
    Connect(anyhow::Error),
    Other(anyhow::Error),
}

pub async fn request(
    host: &str,
    port: u16,
    method: &str,
    path: &str,
    content_type: Option<&str>,
    body: &[u8],
    timeout: Duration,
) -> Result<Reply, Failure> {
    let stream = tokio::time::timeout(Duration::from_secs(2), TcpStream::connect((host, port)))
        .await
        .map_err(|_| Failure::Connect(anyhow!("connect to {host}:{port} timed out")))?
        .map_err(|e| Failure::Connect(anyhow!("connect to {host}:{port}: {e}")))?;
    tokio::time::timeout(timeout, exchange(stream, host, port, method, path, content_type, body))
        .await
        .map_err(|_| Failure::Other(anyhow!("{method} {path} timed out after {}s", timeout.as_secs())))?
        .map_err(Failure::Other)
}

async fn exchange(
    mut stream: TcpStream,
    host: &str,
    port: u16,
    method: &str,
    path: &str,
    content_type: Option<&str>,
    body: &[u8],
) -> Result<Reply> {
    let mut head = format!("{method} {path} HTTP/1.0\r\nHost: {host}:{port}\r\nContent-Length: {}\r\n", body.len());
    if let Some(ct) = content_type {
        head.push_str(&format!("Content-Type: {ct}\r\n"));
    }
    head.push_str("\r\n");
    stream.write_all(head.as_bytes()).await?;
    stream.write_all(body).await?;
    let mut raw = vec![];
    stream.read_to_end(&mut raw).await?;

    let split = raw.windows(4).position(|w| w == b"\r\n\r\n").context("reply has no header end")?;
    let head = String::from_utf8_lossy(&raw[..split]).to_string();
    let mut lines = head.lines();
    let status_line = lines.next().unwrap_or("");
    let Some(status) = status_line.split_whitespace().nth(1).and_then(|s| s.parse().ok()) else {
        bail!("bad status line: {status_line}");
    };
    let content_type = lines
        .filter_map(|l| l.split_once(':'))
        .find(|(k, _)| k.trim().eq_ignore_ascii_case("content-type"))
        .map(|(_, v)| v.trim().to_string());
    Ok(Reply { status, content_type, body: raw[split + 4..].to_vec() })
}
