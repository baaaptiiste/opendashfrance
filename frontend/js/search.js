// Barre de recherche : ville/CP -> géocodage BAN -> contexte global.
// Au succès, met à jour l'état + le bandeau et déclenche un rafraîchissement
// de tous les widgets via le callback fourni.

import { geocode } from "./api.js";
import { setLocation, state } from "./state.js";

export function initSearch(onLocationChange) {
  const form = document.getElementById("search-form");
  const input = document.getElementById("search-input");
  const bar = document.getElementById("location-bar");

  // Affiche la localisation déjà enregistrée au chargement.
  if (state.location) showBar(bar, state.location);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;

    bar.classList.remove("hidden");
    bar.textContent = "Recherche…";

    const loc = await geocode(q);
    if (!loc || loc.lat == null) {
      bar.textContent = "Adresse introuvable.";
      return;
    }

    setLocation(loc);
    showBar(bar, loc);
    onLocationChange(loc);
  });
}

function showBar(bar, loc) {
  bar.classList.remove("hidden");
  bar.innerHTML = `📍 <strong>${loc.label || loc.ville || ""}</strong>
    — lat ${loc.lat?.toFixed(4)}, lon ${loc.lon?.toFixed(4)}
    ${loc.code_insee ? `· INSEE ${loc.code_insee}` : ""}`;
}
