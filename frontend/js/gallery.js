// Galerie de widgets : liste les sources du catalogue, groupées par thème,
// avec une case à cocher. Cocher = ajouter le widget, décocher = le retirer.
// Une source non disponible (clé manquante) est grisée et non cochable.

import { addWidget, removeWidget, isActive } from "./dashboard.js";

export function initGallery(catalogue) {
  const body = document.getElementById("gallery-body");
  const gallery = document.getElementById("gallery");
  const toggle = document.getElementById("toggle-gallery");
  const close = document.getElementById("close-gallery");

  toggle.addEventListener("click", () => gallery.classList.toggle("hidden"));
  close.addEventListener("click", () => gallery.classList.add("hidden"));

  // Regroupe par thème.
  const parTheme = {};
  Object.values(catalogue).forEach((s) => {
    (parTheme[s.theme] ||= []).push(s);
  });

  body.innerHTML = "";
  Object.keys(parTheme)
    .sort()
    .forEach((theme) => {
      const bloc = document.createElement("div");
      bloc.className = "gallery-theme";
      bloc.innerHTML = `<h3>${theme}</h3>`;

      parTheme[theme].forEach((s) => {
        const item = document.createElement("div");
        item.className = "gallery-item" + (s.disponible ? "" : " disabled");
        const checked = isActive(s.id) ? "checked" : "";
        const dis = s.disponible ? "" : "disabled";
        item.innerHTML = `
          <input type="checkbox" id="cb-${s.id}" ${checked} ${dis} />
          <label for="cb-${s.id}">
            ${s.nom}
            <span class="meta">
              ${s.description || ""}
              ${s.disponible ? "" : "🔒 clé requise"}
            </span>
          </label>
        `;
        const cb = item.querySelector("input");
        cb.addEventListener("change", () => {
          if (cb.checked) addWidget(s.id);
          else removeWidget(s.id);
        });
        bloc.appendChild(item);
      });
      body.appendChild(bloc);
    });
}
