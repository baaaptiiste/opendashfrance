// Dispatcher de rendu : associe un type de rendu à son renderer.
// Le dashboard appelle render(rendu, body, enveloppe) sans rien savoir
// de la source — c'est le cœur de la modularité côté front.

import { renderStat } from "./stat.js";
import { renderGraphe } from "./graphe.js";
import { renderCarte } from "./carte.js";
import { renderListe } from "./liste.js";
import { renderTableau } from "./tableau.js";

const RENDERERS = {
  stat: renderStat,
  graphe: renderGraphe,
  carte: renderCarte,
  liste: renderListe,
  tableau: renderTableau,
};

export function render(rendu, body, enveloppe) {
  const fn = RENDERERS[rendu];
  if (!fn) {
    body.innerHTML = `<div class="widget-error">Rendu inconnu : ${rendu}</div>`;
    return;
  }
  fn(body, enveloppe);
}
