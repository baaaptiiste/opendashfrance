// État partagé + persistance localStorage.
// - location : contexte géographique courant {lat, lon, code_insee, label}
// - active   : ids des widgets affichés, dans l'ordre (drag & drop)

const LS_ACTIVE = "opendash.active";
const LS_LOCATION = "opendash.location";

export const state = {
  location: load(LS_LOCATION, null),
  active: load(LS_ACTIVE, []),
};

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function setLocation(loc) {
  state.location = loc;
  localStorage.setItem(LS_LOCATION, JSON.stringify(loc));
}

export function saveActive() {
  localStorage.setItem(LS_ACTIVE, JSON.stringify(state.active));
}

export function addActive(id) {
  if (!state.active.includes(id)) {
    state.active.push(id);
    saveActive();
  }
}

export function removeActive(id) {
  state.active = state.active.filter((x) => x !== id);
  saveActive();
}

export function reorderActive(order) {
  state.active = order;
  saveActive();
}
