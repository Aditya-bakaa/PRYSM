async function request(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let description = await res.text();
    try { description = JSON.parse(description).detail || description; } catch { /* preserve server response */ }
    throw new Error(`${res.status}: ${typeof description === 'string' ? description.slice(0, 250) : JSON.stringify(description).slice(0, 250)}`);
  }
  return res.json();
}
export const getHealth = () => request('/api/health');
export const getReference = () => request('/api/reference');
export const getIntegrityDemo = () => request('/api/integrity-demo');
export const runArena = (problem, mode, refresh = false) => request('/api/arena/run', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ problem, mode, refresh }),
});
