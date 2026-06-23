// Gestion de la grille de widgets : ajout/suppression, chargement des données,
// drag & drop, persistance de l'ordre. Ne connaît pas les sources en détail :
// il lit les métadonnées du catalogue et délègue l'affichage aux renderers.

import { fetchData } from "./api.js";
import { render } from "./widgets/index.js";
import {
  state,
  addActive,
  removeActive,
  reorderActive,
} from "./state.js";

let catalogue = {}; // id -> métadonnées source
let grid;

export function initDashboard(cataMap) {
  catalogue = cataMap;
  grid = document.getElementById("dashboard");
  // Restaure les widgets sauvegardés.
  state.active.forEach((id) => mountWidget(id));
  updateEmptyHint();
}

export function addWidget(id) {
  addActive(id);
  mountWidget(id);
  updateEmptyHint();
}

export function removeWidget(id) {
  removeActive(id);
  document.getElementById(`w-${id}`)?.remove();
  updateEmptyHint();
}

export function isActive(id) {
  return state.active.includes(id);
}

// Recharge les données de tous les widgets (ex. après changement de localisation).
export function refreshAll() {
  state.active.forEach((id) => loadWidgetData(id));
}

function updateEmptyHint() {
  const hint = document.getElementById("empty-hint");
  if (hint) hint.classList.toggle("hidden", state.active.length > 0);
}

function mountWidget(id) {
  const meta = catalogue[id];
  if (!meta || document.getElementById(`w-${id}`)) return;

  const el = document.createElement("section");
  el.className = "widget";
  el.id = `w-${id}`;
  el.draggable = true;
  el.dataset.id = id;
  el.innerHTML = `
    <div class="widget-head">
      <h3 class="widget-title">${meta.nom}</h3>
      <button class="widget-close" aria-label="Retirer">×</button>
    </div>
    <div class="widget-body"><div class="widget-loading">Chargement…</div></div>
    <div class="widget-attr">${meta.attribution || ""}</div>
  `;

  el.querySelector(".widget-close").addEventListener("click", () =>
    removeWidget(id)
  );
  attachDnd(el);
  grid.appendChild(el);

  loadWidgetData(id);
}

async function loadWidgetData(id) {
  const meta = catalogue[id];
  const el = document.getElementById(`w-${id}`);
  if (!el) return;
  const body = el.querySelector(".widget-body");
  body.innerHTML = `<div class="widget-loading">Chargement…</div>`;

  const ctx = state.location || {};
  let env;
  try {
    env = await fetchData(id, ctx);
  } catch (e) {
    body.innerHTML = `<div class="widget-error">Erreur réseau</div>`;
    return;
  }

  body.innerHTML = "";
  if (env.disponible === false || env.erreur) {
    body.innerHTML = `<div class="widget-error">${env.erreur || "Indisponible"}</div>`;
    return;
  }
  render(meta.rendu, body, env);
}

// --- Drag & drop (réorganisation de la grille) ---
let dragEl = null;

function attachDnd(el) {
  el.addEventListener("dragstart", (e) => {
    dragEl = el;
    el.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
  });
  el.addEventListener("dragend", () => {
    el.classList.remove("dragging");
    dragEl = null;
    persistOrder();
  });
  el.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!dragEl || dragEl === el) return;
    const rect = el.getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    grid.insertBefore(dragEl, after ? el.nextSibling : el);
  });
}

function persistOrder() {
  const order = [...grid.querySelectorAll(".widget")].map((w) => w.dataset.id);
  reorderActive(order);
}
