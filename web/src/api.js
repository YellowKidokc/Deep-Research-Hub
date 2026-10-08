// All state lives in the hub. The page only asks.
export async function api(path, opts = {}) {
  const res = await fetch(`/api${path}`, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `${res.status} ${res.statusText}`);
  return body;
}

export const post = (path) => api(path, { method: "POST" });
