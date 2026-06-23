// Point d'entrée : charge le catalogue puis câble galerie, recherche, grille.

import { fetchSources } from "./api.js";
import { initDashboard, refreshAll } from "./dashboard.js";
import { initGallery } from "./gallery.js";
import { initSearch } from "./search.js";

async function main() {
  let sources;
  try {
    sources = await fetchSources();
  } catch {
    document.getElementById("empty-hint").textContent =
      "Backend injoignable. Lancez le serveur Flask.";
    return;
  }

  // Index id -> métadonnées, partagé par galerie et dashboard.
  const catalogue = Object.fromEntries(sources.map((s) => [s.id, s]));

  initDashboard(catalogue);
  initGallery(catalogue);
  // Au changement de localisation : recharge tous les widgets actifs.
  initSearch(() => refreshAll());
}

main();
