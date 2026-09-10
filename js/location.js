/* ============================================
   location.js — map, search, coordinates, distance
   ============================================ */

// Prototype-only mock GBB POP data.
// Replace with real GBB fibre POP / GIS data when available.
const gbbPOPs = [
  { name: 'GBB Abuja POP', lat: 9.0765, lng: 7.3986 },
  { name: 'GBB Lagos POP', lat: 6.5244, lng: 3.3792 },
  { name: 'GBB Port Harcourt POP', lat: 4.8156, lng: 7.0498 },
];

/** Haversine distance in metres between two lat/lng points */
function haversineDistanceMetres(lat1, lng1, lat2, lng2) {
  const R = 6371000; // Earth radius in metres
  const toRad = deg => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/** Find the nearest mock POP to a given point */
function nearestPOP(lat, lng) {
  let nearest = null;
  let best = Infinity;
  gbbPOPs.forEach(pop => {
    const d = haversineDistanceMetres(lat, lng, pop.lat, pop.lng);
    if (d < best) { best = d; nearest = pop; }
  });
  return { pop: nearest, distanceMetres: best };
}

/** Parse a coordinate string like "9.0765, 7.3986" or "9.0765 7.3986" */
function parseCoordinateInput(raw) {
  if (!raw) return null;
  const cleaned = raw.trim().replace(/,/g, ' ').replace(/\s+/g, ' ');
  const parts = cleaned.split(' ');
  if (parts.length !== 2) return null;
  const lat = parseFloat(parts[0]);
  const lng = parseFloat(parts[1]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  if (lat < -90 || lat > 90) return null;
  if (lng < -180 || lng > 180) return null;
  return { lat, lng };
}

/**
 * Sets up an interactive location picker on the given map element id.
 * options.onLocationChange(lat, lng) fires whenever the selection changes.
 */
function createLocationPicker(mapElementId, options = {}) {
  const map = L.map(mapElementId, { zoomControl: true }).setView([9.0765, 7.3986], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  // "Locate me" control
  const LocateControl = L.Control.extend({
    options: { position: 'topleft' },
    onAdd: function () {
      const btn = L.DomUtil.create('button', 'leaflet-bar');
      btn.title = 'Use my current location';
      btn.style.width = '30px';
      btn.style.height = '30px';
      btn.style.cursor = 'pointer';
      btn.innerHTML = '📍';
      btn.setAttribute('aria-label', 'Use my current location');
      L.DomEvent.disableClickPropagation(btn);
      btn.addEventListener('click', () => {
        if (!navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition(pos => {
          setCustomerMarker(pos.coords.latitude, pos.coords.longitude);
        });
      });
      return btn;
    },
  });
  map.addControl(new LocateControl());

  const emeraldIcon = L.divIcon({
    className: '',
    html: '<div style="width:16px;height:16px;border-radius:50%;background:#008751;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

  const popIcon = L.divIcon({
    className: '',
    html: '<div style="width:14px;height:14px;border-radius:50%;background:#006B40;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });

  // Show mock POPs
  gbbPOPs.forEach(pop => {
    L.marker([pop.lat, pop.lng], { icon: popIcon }).addTo(map).bindPopup(pop.name);
  });

  let customerMarker = null;
  let routeLine = null;

  function setCustomerMarker(lat, lng) {
    if (customerMarker) {
      customerMarker.setLatLng([lat, lng]);
    } else {
      customerMarker = L.marker([lat, lng], { icon: emeraldIcon }).addTo(map);
    }
    map.setView([lat, lng], 14);

    const { pop, distanceMetres } = nearestPOP(lat, lng);

    if (routeLine) map.removeLayer(routeLine);
    routeLine = L.polyline(
      [[lat, lng], [pop.lat, pop.lng]],
      { color: '#008751', weight: 3, dashArray: '6 6' }
    ).addTo(map);

    if (typeof options.onLocationChange === 'function') {
      options.onLocationChange({ lat, lng, nearestPop: pop, distanceMetres });
    }
  }

  map.on('click', e => setCustomerMarker(e.latlng.lat, e.latlng.lng));

  return { map, setCustomerMarker };
}

/** Free-text location search using OpenStreetMap Nominatim (no key required) */
async function searchLocationText(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(query)}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('Search failed');
  const data = await res.json();
  return data.map(item => ({
    label: item.display_name,
    lat: parseFloat(item.lat),
    lng: parseFloat(item.lon),
  }));
}
