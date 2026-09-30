// LocationStep.jsx
// -----------------------------------------------------------------------------
// Step 1 of the estimator.
//
// Responsibilities:
//   1. Display the Leaflet map.
//   2. Show the mock GBB POPs.
//   3. Let the user click the map.
//   4. Let the user search a place using Nominatim/OpenStreetMap.
//   5. Let the user enter coordinates directly.
//   6. Find the nearest mock POP.
//   7. Calculate straight-line distance using Haversine.
//   8. Send the resulting location/distance back to App.
//
// IMPORTANT:
// This is still prototype logic. The displayed line is a straight line to
// the nearest mock POP. It is NOT the real fibre route through GBB assets.
// -----------------------------------------------------------------------------

import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import {
  gbbPOPs,
  nearestPOP,
  parseCoordinateInput,
  searchLocationText,
} from '../services/location'

// Leaflet's normal marker icon can require extra asset configuration in Vite.
// These custom div icons avoid that problem and keep the prototype simple.
const customerIcon = L.divIcon({
  className: '',
  html: '<div style="width:16px;height:16px;border-radius:50%;background:#008751;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

const popIcon = L.divIcon({
  className: '',
  html: '<div style="width:14px;height:14px;border-radius:50%;background:#006B40;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4);"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

export default function LocationStep({ draft, setDraft, onContinue }) {
  // A ref gives us direct access to the <div> where Leaflet should create
  // the map. React refs are useful when a non-React library needs a DOM node.
  const mapRef = useRef(null)

  // Stores the Leaflet map object after it has been created.
  const mapInstance = useRef(null)

  // Stores the customer's Leaflet marker so it can be moved instead of
  // creating a new marker every time the customer changes location.
  const markerRef = useRef(null)

  // Stores the temporary straight-line route shown on the prototype map.
  const routeRef = useRef(null)

  // Local UI state. These values only matter to this component.
  const [search, setSearch] = useState('')
  const [results, setResults] = useState([])
  const [coordinate, setCoordinate] = useState('')
  const [coordinateError, setCoordinateError] = useState(false)
  const [searching, setSearching] = useState(false)

  // Create the Leaflet map once when the component mounts.
  useEffect(() => {
    // React StrictMode can cause development-only mount/cleanup cycles.
    // This guard prevents us from creating two maps on the same DOM element.
    if (!mapRef.current || mapInstance.current) return

    // Create the map and give Abuja a sensible initial view.
    const map = L.map(mapRef.current, { zoomControl: true }).setView(
      [9.0765, 7.3986],
      12,
    )

    // OpenStreetMap supplies the visible map tiles.
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    // Add the current prototype POP list to the map.
    gbbPOPs.forEach(pop =>
      L.marker([pop.lat, pop.lng], { icon: popIcon })
        .addTo(map)
        .bindPopup(pop.name),
    )

    // Leaflet does not provide this custom "locate me" button by default in
    // the exact form we want, so we create a small Leaflet control ourselves.
    const LocateControl = L.Control.extend({
      options: { position: 'topleft' },

      onAdd() {
        const btn = L.DomUtil.create('button', 'leaflet-bar')

        btn.title = 'Use my current location'
        btn.style.width = '30px'
        btn.style.height = '30px'
        btn.style.cursor = 'pointer'
        btn.innerHTML = '📍'
        btn.setAttribute('aria-label', 'Use my current location')

        // Prevent clicking the control from also triggering the map's
        // normal click handler.
        L.DomEvent.disableClickPropagation(btn)

        btn.addEventListener('click', () => {
          if (!navigator.geolocation) return

          navigator.geolocation.getCurrentPosition(pos =>
            setCustomerMarker(
              pos.coords.latitude,
              pos.coords.longitude,
            ),
          )
        })

        return btn
      },
    })

    map.addControl(new LocateControl())

    // Central function for selecting a customer location.
    //
    // This function:
    //   - moves/creates the customer marker
    //   - centers the map
    //   - finds the nearest mock POP
    //   - draws the prototype straight line
    //   - updates the shared draft in App
    const setCustomerMarker = (lat, lng) => {
      if (markerRef.current) {
        markerRef.current.setLatLng([lat, lng])
      } else {
        markerRef.current = L.marker([lat, lng], {
          icon: customerIcon,
        }).addTo(map)
      }

      map.setView([lat, lng], 14)

      const { pop, distanceMetres } = nearestPOP(lat, lng)

      if (routeRef.current) {
        map.removeLayer(routeRef.current)
      }

      routeRef.current = L.polyline(
        [[lat, lng], [pop.lat, pop.lng]],
        {
          color: '#008751',
          weight: 3,
          dashArray: '6 6',
        },
      ).addTo(map)

      // setDraft uses the functional form because the new draft depends on
      // the previous draft object. React then re-renders App and its children.
      setDraft(current => ({
        ...current,
        lat,
        lng,
        distanceMetres,
        nearestPopName: pop.name,
      }))
    }

    // Clicking anywhere on the map is another way to choose the site.
    map.on('click', e =>
      setCustomerMarker(e.latlng.lat, e.latlng.lng),
    )

    // Store the map and the location-selection function for later event
    // handlers such as search results and coordinate input.
    mapInstance.current = { map, setCustomerMarker }

    // Cleanup is important because Leaflet creates DOM/event listeners
    // outside React. Removing the map prevents leaks and duplicate maps.
    return () => {
      map.remove()
      mapInstance.current = null
    }
  }, [setDraft])

  // Search for a place after the user has entered at least three characters.
  // A 400ms debounce prevents an API request on every single keystroke.
  useEffect(() => {
    const query = search.trim()

    if (query.length < 3) {
      setResults([])
      return
    }

    const timer = setTimeout(async () => {
      setSearching(true)

      try {
        setResults(await searchLocationText(query))
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 400)

    // If the user types again before 400ms, cancel the previous timer.
    return () => clearTimeout(timer)
  }, [search])

  // Select one of the search results and feed it through the same map logic
  // used by clicks and the geolocation button.
  const selectLocation = (lat, lng, label = '') => {
    mapInstance.current?.setCustomerMarker(lat, lng)
    setSearch(label)
    setResults([])
  }

  // Validate coordinates as the user types.
  const handleCoordinateChange = event => {
    const value = event.target.value
    setCoordinate(value)

    if (!value.trim()) {
      setCoordinateError(false)
      return
    }

    const coords = parseCoordinateInput(value)

    if (!coords) {
      setCoordinateError(true)
      return
    }

    setCoordinateError(false)
    selectLocation(coords.lat, coords.lng)
  }

  // The Continue button is enabled only when App has a valid location and
  // calculated distance.
  const hasLocation =
    Number.isFinite(draft.lat) &&
    Number.isFinite(draft.lng) &&
    Number.isFinite(draft.distanceMetres)

  const km = hasLocation
    ? (draft.distanceMetres / 1000).toFixed(2)
    : '—'

  return (
    <section className="step-panel">
      <div className="card">
        <h1>Where is your site located?</h1>
        <p className="muted">
          Search or click on the map to select your site
        </p>

        <div className="field" style={{ marginTop: 18 }}>
          <label htmlFor="location-search">Search location</label>

          <div className="input-with-icon">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>

            <input
              id="location-search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search location..."
              autoComplete="off"
            />
          </div>

          {search.trim().length >= 3 && (
            <div id="search-results" style={{ marginTop: 6 }}>
              {searching && (
                <p className="muted">Searching...</p>
              )}

              {results.map(result => (
                <button
                  key={`${result.lat}-${result.lng}`}
                  type="button"
                  className="btn btn-secondary"
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    marginBottom: 6,
                    fontWeight: 400,
                  }}
                  onClick={() =>
                    selectLocation(
                      result.lat,
                      result.lng,
                      result.label,
                    )
                  }
                >
                  {result.label}
                </button>
              ))}

              {!searching && !results.length && (
                <p className="muted">
                  Search unavailable or no matching location found.
                </p>
              )}
            </div>
          )}
        </div>

        <div className={`field ${coordinateError ? 'error' : ''}`}>
          <label htmlFor="coordinate-input">
            Or enter coordinates directly
          </label>

          <input
            id="coordinate-input"
            value={coordinate}
            onChange={handleCoordinateChange}
            placeholder="e.g. 9.0765, 7.3986"
          />

          <div className="field-error-msg">
            Please enter valid coordinates. Example: 9.0765, 7.3986
          </div>
        </div>

        <div className="map-wrap">
          <div id="map" ref={mapRef} />
        </div>

        <div className="step-actions">
          {hasLocation && (
            <div className="distance-box">
              <div className="muted">Estimated Fibre Distance</div>

              <div className="value">
                {km} km ({Math.round(draft.distanceMetres)} m)
              </div>

              <div
                className="muted"
                style={{
                  marginTop: 2,
                  fontSize: 11.5,
                }}
              >
                Straight-line distance to nearest mock GBB POP — not an
                engineered route.
              </div>
            </div>
          )}

          <div style={{ flex: 1 }} />

          <button
            className="btn btn-primary"
            disabled={!hasLocation}
            onClick={onContinue}
          >
            Continue →
          </button>
        </div>
      </div>
    </section>
  )
}
