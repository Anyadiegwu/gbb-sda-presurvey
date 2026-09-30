// location.js
// -----------------------------------------------------------------------------
// Location/network helper functions.
//
// Current prototype:
//   customer location → nearest MOCK GBB POP → Haversine straight-line distance
//
// Production target:
//   customer location → nearest usable GBB network asset (e.g. FAT/FDT/manhole)
//   → actual network topology → engineered fibre path distance
//
// This file is intentionally isolated so the location engine can later be
// replaced without rewriting the React UI.
// -----------------------------------------------------------------------------

// Temporary prototype POP data.
// These coordinates are not a complete representation of the GBB network.
export const gbbPOPs = [
  { name: 'GBB Abuja POP', lat: 9.0765, lng: 7.3986 },
  { name: 'GBB Lagos POP', lat: 6.5244, lng: 3.3792 },
  { name: 'GBB Port Harcourt POP', lat: 4.8156, lng: 7.0498 },
]

// Calculate great-circle distance between two latitude/longitude points.
//
// Haversine is useful for geographic straight-line distance. It does NOT know
// anything about roads, fibre cables, ducts, manholes or network topology.
export function haversineDistanceMetres(
  lat1,
  lng1,
  lat2,
  lng2,
) {
  // Approximate radius of Earth in metres.
  const R = 6371000

  // JavaScript trigonometric functions expect radians rather than degrees.
  const toRad = deg => (deg * Math.PI) / 180

  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLng / 2) ** 2

  return (
    R *
    2 *
    Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a),
    )
  )
}

// Find the POP with the smallest Haversine distance to the customer.
export function nearestPOP(lat, lng) {
  return gbbPOPs.reduce(
    (best, pop) => {
      const distanceMetres =
        haversineDistanceMetres(
          lat,
          lng,
          pop.lat,
          pop.lng,
        )

      return distanceMetres < best.distanceMetres
        ? { pop, distanceMetres }
        : best
    },
    {
      pop: null,
      distanceMetres: Infinity,
    },
  )
}

// Convert text such as:
//   "9.0765, 7.3986"
// into:
//   { lat: 9.0765, lng: 7.3986 }
//
// Invalid coordinates return null.
export function parseCoordinateInput(raw) {
  if (!raw) return null

  // Normalize commas and repeated whitespace so several common formats work.
  const parts = raw
    .trim()
    .replace(/,/g, ' ')
    .replace(/\s+/g, ' ')
    .split(' ')

  if (parts.length !== 2) return null

  const lat = parseFloat(parts[0])
  const lng = parseFloat(parts[1])

  if (
    !Number.isFinite(lat) ||
    !Number.isFinite(lng)
  ) {
    return null
  }

  // Latitude must be between -90 and 90.
  // Longitude must be between -180 and 180.
  if (
    lat < -90 ||
    lat > 90 ||
    lng < -180 ||
    lng > 180
  ) {
    return null
  }

  return { lat, lng }
}

// Search a human-readable location using Nominatim's OpenStreetMap service.
//
// The function is async because fetch() returns a Promise.
export async function searchLocationText(query) {
  const url =
    `https://nominatim.openstreetmap.org/search?format=json&limit=5&q=${encodeURIComponent(query)}`

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error('Search failed')
  }

  const data = await response.json()

  // Convert Nominatim's response shape into the smaller shape the UI needs.
  return data.map(item => ({
    label: item.display_name,
    lat: parseFloat(item.lat),
    lng: parseFloat(item.lon),
  }))
}
