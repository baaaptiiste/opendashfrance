// Client de l'API backend. Une seule responsabilité : parler à /api/*.

const BASE = "/api";

export async function fetchSources() {
  const r = await fetch(`${BASE}/sources`);
  if (!r.ok) throw new Error("Catalogue indisponible");
  return r.json();
}

export async function geocode(q) {
  const r = await fetch(`${BASE}/geocode?q=${encodeURIComponent(q)}`);
  if (!r.ok) return null;
  return r.json();
}

export async function fetchData(sourceId, ctx = {}) {
  const params = new URLSearchParams();
  if (ctx.lat != null) params.set("lat", ctx.lat);
  if (ctx.lon != null) params.set("lon", ctx.lon);
  if (ctx.code_insee) params.set("code_insee", ctx.code_insee);
  if (ctx.code_postal) params.set("code_postal", ctx.code_postal);
  if (ctx.q) params.set("q", ctx.q);
  const r = await fetch(`${BASE}/data/${sourceId}?${params.toString()}`);
  return r.json(); // le backend renvoie toujours une enveloppe (même en erreur)
}
