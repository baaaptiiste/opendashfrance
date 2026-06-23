// Renderer "graphe" : Chart.js. Enveloppe attendue :
//   data: { type:"line|bar", labels:[], series:[{nom, points:[]}] }

export function renderGraphe(body, env) {
  const d = env.data || {};
  const canvas = document.createElement("canvas");
  body.appendChild(canvas);

  const palette = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"];
  const datasets = (d.series || []).map((s, i) => ({
    label: s.nom,
    data: s.points,
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length] + "33",
    tension: 0.3,
    pointRadius: 0,
    fill: d.type === "line",
  }));

  // eslint-disable-next-line no-undef
  new Chart(canvas, {
    type: d.type === "bar" ? "bar" : "line",
    data: { labels: d.labels || [], datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: "#9aa7b4" } } },
      scales: {
        x: { ticks: { color: "#9aa7b4", maxTicksLimit: 8 }, grid: { color: "#2c3845" } },
        y: { ticks: { color: "#9aa7b4" }, grid: { color: "#2c3845" } },
      },
    },
  });
}
