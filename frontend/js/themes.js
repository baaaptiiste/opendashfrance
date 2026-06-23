// Métadonnées visuelles par thème : icône (emoji) + couleur d'accent.
// Partagé par la galerie et l'en-tête des widgets pour une identité cohérente.

export const THEME_META = {
  énergie: { icon: "⛽", color: "#f59e0b" },
  eau: { icon: "💧", color: "#38bdf8" },
  météo: { icon: "🌤️", color: "#60a5fa" },
  société: { icon: "🏛️", color: "#a78bfa" },
  immobilier: { icon: "🏠", color: "#fb7185" },
  culture: { icon: "🎭", color: "#f472b6" },
  alimentation: { icon: "🍎", color: "#34d399" },
};

const FALLBACK = { icon: "📊", color: "#3b82f6" };

export function themeMeta(theme) {
  return THEME_META[theme] || FALLBACK;
}

// Couleur sémantique d'un indice de qualité de l'air européen (0 → 100+).
export function aqiColor(aqi) {
  if (aqi == null) return "#9aa7b4";
  if (aqi <= 20) return "#22c55e";
  if (aqi <= 40) return "#84cc16";
  if (aqi <= 60) return "#eab308";
  if (aqi <= 80) return "#f97316";
  if (aqi <= 100) return "#ef4444";
  return "#a21caf";
}

// Couleur officielle d'un Nutri-Score (A → E).
export function nutriColor(grade) {
  return (
    {
      A: "#038141",
      B: "#85bb2f",
      C: "#fecb02",
      D: "#ee8100",
      E: "#e63e11",
    }[(grade || "").toUpperCase()] || "#5b6675"
  );
}
