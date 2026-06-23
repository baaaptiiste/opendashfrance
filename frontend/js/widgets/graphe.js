// Renderer "graphe" : Chart.js + bandeau de résumé (actuel / min / max) pour
// lire l'essentiel sans déchiffrer la courbe. Enveloppe :
//   data: { type:"line|bar", labels:[], series:[{nom, points:[]}] }

export function renderGraphe(body, env, meta = {}) {
  const d = env.data || {};
  const accent = meta.color || "#4c8dff";
  const serie = (d.series || [])[0];
  const pts = (serie?.points || []).filter((p) => p != null);

  // Bandeau résumé dérivé de la 1re série (actuel = 1er point).
  let resume = "";
  if (pts.length) {
    const actuel = pts[0];
    const min = Math.min(...pts);
    const max = Math.max(...pts);
    const u = (serie.nom.match(/\(([^)]+)\)/) || [, ""])[1];
    resume = `
      <div class="summary">
        <div class="chip big"><span>Actuel</span><strong>${actuel}${u}</strong></div>
        <div class="chip"><span>Min</span><strong>${min}${u}</strong></div>
        <div class="chip"><span>Max</span><strong>${max}${u}</strong></div>
      </div>`;
  }

  body.innerHTML = resume + `<div class="graph-wrap"><canvas></canvas></div>`;
  const canvas = body.querySelector("canvas");

  const ctx = canvas.getContext("2d");
  const grad = ctx.createLinearGradient(0, 0, 0, 200);
  grad.addColorStop(0, accent + "55");
  grad.addColorStop(1, accent + "00");

  const datasets = (d.series || []).map((s, i) => ({
    label: s.nom,
    data: s.points,
    borderColor: i === 0 ? accent : "#34d399",
    backgroundColor: d.type === "bar" ? accent + "cc" : grad,
    borderWidth: 2,
    tension: 0.4,
    pointRadius: 0,
    pointHoverRadius: 4,
    fill: d.type !== "bar",
  }));

  // eslint-disable-next-line no-undef
  new Chart(canvas, {
    type: d.type === "bar" ? "bar" : "line",
    data: { labels: d.labels || [], datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: "#93a1b2", maxTicksLimit: 6, font: { size: 10 } },
          grid: { display: false },
        },
        y: {
          ticks: { color: "#93a1b2", font: { size: 10 } },
          grid: { color: "#232c3955" },
        },
      },
    },
  });
}
