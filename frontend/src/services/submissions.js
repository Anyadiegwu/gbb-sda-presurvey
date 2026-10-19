// submissions.js
// -----------------------------------------------------------------------------
// Sends the customer's request to the backend (replaces the old
// localStorage-based storage.js).
//
// POST /submissions/  →  the backend creates the record and generates the
// reference number (e.g. GBB-2026-000123).
// -----------------------------------------------------------------------------

import { apiRequest } from './api'

export async function submitRequest({ form, draft, calc }) {
  const body = {
    // Contact details
    fullName: form.fullName.trim(),
    company: form.company.trim() || null,
    email: form.email.trim(),
    phone: form.phone.trim(),
    siteAddress: form.siteAddress.trim(),
    notes: form.notes.trim() || null,

    // Location result (from /quotes/resolve-location)
    manholeId: calc.manholeId,
    customerToManholeMeters: draft.customerToManholeMeters ?? 0,
    fiberlineRouteId: draft.fiberlineRouteId ?? null,
    manholeToFiberlineMeters: draft.manholeToFiberlineMeters ?? 0,
    totalDistanceMeters: calc.totalDistanceMeters,
    routePolyline: draft.routePolyline ?? null,

    // Requirements
    bandwidthMbps: calc.bandwidthMbps,
    providesOwnRack: Boolean(draft.providesOwnRack),

    // Quote (from /quotes/calculate)
    nrcItems: calc.nrcRows,
    arcItems: calc.arcRows,
    totalNRC: calc.totalNRC,
    totalARC: calc.totalARC,
    grandTotal: calc.grandTotal,
  }

  // Trailing slash matters: the route is defined as "/submissions/".
  return apiRequest('/submissions/', { method: 'POST', body })
}
