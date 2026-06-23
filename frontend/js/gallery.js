// Galerie de widgets : sources groupées par thème, avec icône et pastille
// de couleur. Cocher = ajouter le widget, décocher = le retirer. Une source
// non disponible (clé manquante) est grisée et non cochable.

import { addWidget, removeWidget, isActive } from "./dashboard.js";
import { themeMeta } from "./themes.js";

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
      const tm = themeMeta(theme);
      const bloc = document.createElement("div");
      bloc.className = "gallery-theme";
      bloc.innerHTML = `<h3><span class="dot" style="background:${tm.color}"></span>${theme}</h3>`;

      parTheme[theme].forEach((s) => {
        const item = document.createElement("div");
        const checked = isActive(s.id);
        item.className =
          "gallery-item" +
          (s.disponible ? "" : " disabled") +
          (checked ? " checked" : "");
        const dis = s.disponible ? "" : "disabled";
        item.innerHTML = `
          <span class="gi-icon">${tm.icon}</span>
          <span class="gi-text">
            <span class="gi-name">${s.nom}</span>
            <span class="gi-desc">${s.description || ""}${
              s.disponible ? "" : " · 🔒 clé requise"
            }</span>
          </span>
          <input type="checkbox" id="cb-${s.id}" ${checked ? "checked" : ""} ${dis} />
        `;
        const cb = item.querySelector("input");
        const apply = () => {
          if (cb.checked) {
            addWidget(s.id);
            item.classList.add("checked");
          } else {
            removeWidget(s.id);
            item.classList.remove("checked");
          }
        };
        cb.addEventListener("change", apply);
        // Clic n'importe où sur la carte bascule la case (hors clic direct case).
        item.addEventListener("click", (e) => {
          if (e.target !== cb && !cb.disabled) {
            cb.checked = !cb.checked;
            apply();
          }
        });
        bloc.appendChild(item);
      });
      body.appendChild(bloc);
    });
}
