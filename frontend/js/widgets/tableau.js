// Renderer "tableau". Enveloppe attendue :
//   data: { colonnes:[], lignes:[[]] }

export function renderTableau(body, env) {
  const d = env.data || {};
  const table = document.createElement("table");
  table.className = "tableau";

  const thead = `<thead><tr>${(d.colonnes || [])
    .map((c) => `<th>${c}</th>`)
    .join("")}</tr></thead>`;

  const rows = (d.lignes || [])
    .map(
      (ligne) =>
        `<tr>${ligne.map((cell) => `<td>${cell ?? ""}</td>`).join("")}</tr>`
    )
    .join("");

  table.innerHTML = `${thead}<tbody>${rows}</tbody>`;
  body.appendChild(table);
}
