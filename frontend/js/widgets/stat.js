// Renderer "stat" : une grande valeur + label. Générique, aucune connaissance
// de la source — lit seulement l'enveloppe { data: {valeur, unite, label} }.

export function renderStat(body, env) {
  const d = env.data || {};
  const valeur = d.valeur ?? "—";
  const fmt =
    typeof valeur === "number" ? valeur.toLocaleString("fr-FR") : valeur;
  body.innerHTML = `
    <div>
      <span class="stat-value">${fmt}</span>
      <span class="stat-unit">${d.unite ?? ""}</span>
    </div>
    <div class="stat-label">${d.label ?? ""}</div>
  `;
}
