// Relays requests from youtube.com to the local Python server
// (content scripts can't reliably call localhost directly).
const SERVER = "http://127.0.0.1:8765";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  fetch(SERVER + msg.path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(msg.body),
  })
    .then((r) => r.json())
    .then((data) => sendResponse({ ok: true, data }))
    .catch((err) => sendResponse({ ok: false, error: String(err) }));
  return true; // async response
});
