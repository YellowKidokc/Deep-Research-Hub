// All state lives in the hub. The page only asks.
export async function api(path, opts = {}) {
  const res = await fetch(`/api${path}`, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `${res.status} ${res.statusText}`);
  return body;
}

export const post = (path) => api(path, { method: "POST" });

// Every AI call goes here: the hub passes it to Forge, which holds the keys.
// Never call a model provider from the page. If Forge is down this throws
// with the hub's "Forge is down" message.
export const forge = (path, opts = {}) => api(`/forge${path}`, opts);
