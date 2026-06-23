// Renderer "tableau" : colonne "Nutri-Score" rendue en badge coloré officiel.
// Enveloppe : data: { colonnes:[], lignes:[[]] }

import { nutriColor } from "../themes.js";

export function renderTableau(body, env, meta = {}) {
  const d = env.data || {};
  const colonnes = d.colonnes || [];
  const nutriIdx = colonnes.findIndex((c) => /nutri/i.test(c));

  const wrap = document.createElement("div");
  wrap.className = "tableau-wrap";
  const table = document.createElement("table");
  table.className = "tableau";

  const thead = `<thead><tr>${colonnes
    .map((c) => `<th>${c}</th>`)
    .join("")}</tr></thead>`;

  const rows = (d.lignes || [])
    .map((ligne) => {
      const cells = ligne
        .map((cell, i) => {
          if (i === nutriIdx && cell && cell !== "?") {
            const c = nutriColor(cell);
            return `<td><span class="nutri" style="background:${c}">${cell}</span></td>`;
          }
          return `<td>${cell ?? ""}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  table.innerHTML = `${thead}<tbody>${rows}</tbody>`;
  wrap.appendChild(table);
  body.appendChild(wrap);
}
