// Renderer "liste". Enveloppe attendue :
//   data: { items:[{titre, sous_titre?, valeur?}] }

export function renderListe(body, env) {
  const items = env.data?.items || [];
  const ul = document.createElement("ul");
  ul.className = "liste";
  if (!items.length) {
    ul.innerHTML = `<li class="sous">Aucun résultat</li>`;
  }
  items.forEach((it) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div>${it.titre ?? ""} ${it.valeur != null ? `<strong>${it.valeur}</strong>` : ""}</div>
      ${it.sous_titre ? `<div class="sous">${it.sous_titre}</div>` : ""}
    `;
    ul.appendChild(li);
  });
  body.appendChild(ul);
}
