// Detects each YouTube video you open, logs it, and shows a download prompt.
let lastId = null;

function currentVideoId() {
  const u = new URL(location.href);
  if (u.pathname === "/watch") return u.searchParams.get("v");
  const m = u.pathname.match(/^\/shorts\/([\w-]{11})/);
  return m ? m[1] : null;
}

function send(path, body) {
  return new Promise((resolve) =>
    chrome.runtime.sendMessage({ path, body }, (res) => resolve(res || { ok: false }))
  );
}

function metadata() {
  const title =
    document.querySelector("h1.ytd-watch-metadata yt-formatted-string")?.textContent ||
    document.title.replace(/ - YouTube$/, "");
  const channel =
    document.querySelector("ytd-watch-metadata ytd-channel-name a")?.textContent ||
    document.querySelector("#owner #channel-name a")?.textContent || "";
  return { title: title.trim(), channel: channel.trim() };
}

function showPrompt(video) {
  document.getElementById("ytwl-prompt")?.remove();
  const box = document.createElement("div");
  box.id = "ytwl-prompt";
  box.style.cssText =
    "position:fixed;right:20px;bottom:20px;z-index:999999;background:#212121;color:#fff;" +
    "padding:14px 16px;border-radius:10px;box-shadow:0 4px 20px #0008;font:14px Roboto,Arial;max-width:340px";
  box.innerHTML = `
    <div style="margin-bottom:10px">Download this video?<br>
      <b style="display:block;margin-top:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></b></div>
    <button data-a="yes" style="background:#c00;color:#fff;border:0;padding:6px 12px;border-radius:6px;cursor:pointer">Download</button>
    <button data-a="no"  style="background:#444;color:#fff;border:0;padding:6px 12px;border-radius:6px;cursor:pointer;margin-left:6px">Not now</button>
    <span id="ytwl-msg" style="margin-left:8px;color:#aaa"></span>`;
  box.querySelector("b").textContent = video.title || video.video_id;
  document.body.appendChild(box);

  const timer = setTimeout(() => box.remove(), 20000); // auto-hide; stays in log as "watched"
  box.addEventListener("click", async (e) => {
    const a = e.target.dataset.a;
    if (!a) return;
    clearTimeout(timer);
    if (a === "yes") {
      const r = await send("/api/download", video);
      box.querySelector("#ytwl-msg").textContent = r.ok ? "Queued ✓" : "Server offline";
    } else {
      await send("/api/skip", video);
      box.querySelector("#ytwl-msg").textContent = "Skipped";
    }
    setTimeout(() => box.remove(), 1500);
  });
}

async function check() {
  const id = currentVideoId();
  if (!id || id === lastId) return;
  lastId = id;
  // wait for title to render after SPA navigation
  await new Promise((r) => setTimeout(r, 2500));
  if (currentVideoId() !== id) return;
  const video = { video_id: id, url: `https://www.youtube.com/watch?v=${id}`, ...metadata() };
  const res = await send("/api/watch", video);
  if (res.ok && res.data.ask) showPrompt(video);
}

// YouTube is a single-page app: listen for its navigation event + poll as backup
window.addEventListener("yt-navigate-finish", check);
setInterval(check, 3000);
check();
