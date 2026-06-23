// Renderer "stat" : une grande valeur lisible immédiatement, + badge coloré
// sémantique quand pertinent (qualité de l'air, Nutri-Score…).

import { aqiColor } from "../themes.js";

export function renderStat(body, env, meta = {}) {
  const d = env.data || {};
  const valeur = d.valeur ?? "—";
  const fmt =
    typeof valeur === "number" ? valeur.toLocaleString("fr-FR") : valeur;

  // Couleur sémantique : AQI -> échelle qualité ; sinon accent du thème.
  let couleur = "var(--w-accent)";
  let badge = "";
  if (d.unite === "AQI" && typeof valeur === "number") {
    couleur = aqiColor(valeur);
    const niveau = (d.label || "").split(" (")[0];
    badge = `<span class="stat-badge" style="background:${couleur}">${niveau}</span>`;
  }

  body.innerHTML = `
    <div class="stat">
      <div>
        <span class="stat-value" style="color:${couleur}">${fmt}</span>
        <span class="stat-unit">${d.unite ?? ""}</span>
      </div>
      <div class="stat-label">${d.label ?? ""}</div>
      ${badge}
    </div>
  `;
}
