// Renderer "carte" : Leaflet. Enveloppe attendue :
//   data: { centre:[lat,lon], markers:[{lat,lon,popup}], geojson? }

export function renderCarte(body, env) {
  const d = env.data || {};
  const div = document.createElement("div");
  div.className = "carte";
  body.appendChild(div);

  const centre = d.centre || [46.6, 2.4]; // centre France par défaut

  // Leaflet a besoin que le conteneur soit dans le DOM avec une taille :
  // on initialise au prochain tick.
  requestAnimationFrame(() => {
    // eslint-disable-next-line no-undef
    const map = L.map(div).setView(centre, d.markers?.length ? 13 : 6);
    // eslint-disable-next-line no-undef
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap",
      maxZoom: 19,
    }).addTo(map);

    (d.markers || []).forEach((m) => {
      // eslint-disable-next-line no-undef
      const marker = L.marker([m.lat, m.lon]).addTo(map);
      if (m.popup) marker.bindPopup(m.popup);
    });

    if (d.geojson) {
      // eslint-disable-next-line no-undef
      L.geoJSON(d.geojson).addTo(map);
    }

    // Recalcule la taille après affichage (widget redimensionné).
    setTimeout(() => map.invalidateSize(), 200);
  });
}
