// Renderer "liste" : chaque entrée a une pastille (initiale ou date) pour
// repérer visuellement. Enveloppe :
//   data: { items:[{titre, sous_titre?, valeur?}] }

export function renderListe(body, env, meta = {}) {
  const items = env.data?.items || [];
  const ul = document.createElement("ul");
  ul.className = "liste";

  if (!items.length) {
    ul.innerHTML = `<li class="sous">Aucun résultat</li>`;
  }

  items.forEach((it) => {
    // Pastille : jour du mois si sous_titre est une date ISO, sinon initiale.
    const m = (it.sous_titre || "").match(/^\d{4}-\d{2}-(\d{2})$/);
    const pastille = m ? m[1] : (it.titre || "?").trim().charAt(0).toUpperCase();

    const li = document.createElement("li");
    li.innerHTML = `
      <span class="avatar">${pastille}</span>
      <span class="li-main">
        <span class="li-titre">${it.titre ?? ""}</span>
        ${it.sous_titre ? `<span class="sous">${it.sous_titre}</span>` : ""}
      </span>
      ${it.valeur != null ? `<span class="li-val">${it.valeur}</span>` : ""}
    `;
    ul.appendChild(li);
  });

  body.appendChild(ul);
}
