// Renderer "carte" : Leaflet, fond sombre, badge de comptage, auto-zoom sur
// les marqueurs. Enveloppe :
//   data: { centre:[lat,lon], markers:[{lat,lon,popup}], geojson? }

export function renderCarte(body, env, meta = {}) {
  const d = env.data || {};
  const accent = meta.color || "#4c8dff";
  const markers = d.markers || [];

  const div = document.createElement("div");
  div.className = "carte";
  if (markers.length) {
    const badge = document.createElement("div");
    badge.className = "carte-badge";
    badge.textContent = `📍 ${markers.length} point${markers.length > 1 ? "s" : ""}`;
    div.appendChild(badge);
  }
  body.appendChild(div);

  const centre = d.centre || [46.6, 2.4];

  requestAnimationFrame(() => {
    // eslint-disable-next-line no-undef
    const map = L.map(div, { zoomControl: true, attributionControl: false }).setView(
      centre,
      markers.length ? 13 : 6
    );
    // Fond sombre pour coller au thème.
    // eslint-disable-next-line no-undef
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      { maxZoom: 19, attribution: "© OpenStreetMap, © CARTO" }
    ).addTo(map);

    const latlngs = [];
    markers.forEach((m) => {
      // eslint-disable-next-line no-undef
      const marker = L.circleMarker([m.lat, m.lon], {
        radius: 7,
        color: "#fff",
        weight: 1.5,
        fillColor: accent,
        fillOpacity: 0.9,
      }).addTo(map);
      if (m.popup) marker.bindPopup(m.popup);
      latlngs.push([m.lat, m.lon]);
    });

    if (d.geojson) {
      // eslint-disable-next-line no-undef
      L.geoJSON(d.geojson, { style: { color: accent } }).addTo(map);
    }

    // Cadre auto sur l'ensemble des points.
    if (latlngs.length > 1) {
      map.fitBounds(latlngs, { padding: [30, 30] });
    }

    setTimeout(() => map.invalidateSize(), 200);
  });
}
