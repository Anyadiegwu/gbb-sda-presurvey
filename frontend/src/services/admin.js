// admin.js
// -----------------------------------------------------------------------------
// Admin API calls: login + BOQ item management.
//
// The backend stores prices as "BOQ items". The four built-ins have the keys
// fibre, rack, router and bandwidth; anything with isCustom = true was added
// by an admin.
// -----------------------------------------------------------------------------

import { apiRequest, setToken } from './api'

// POST /auth/login  →  stores the JWT for later admin requests.
export async function loginAdmin(email, password) {
  const data = await apiRequest('/auth/login', {
    method: 'POST',
    body: { email, password },
  })

  setToken(data.accessToken)
}

// GET /admin/boq-items/
export const listBoqItems = () =>
  apiRequest('/admin/boq-items/', { auth: true })

// POST /admin/boq-items/
export const createBoqItem = payload =>
  apiRequest('/admin/boq-items/', { method: 'POST', body: payload, auth: true })

// PATCH /admin/boq-items/{id}
export const updateBoqItem = (id, payload) =>
  apiRequest(`/admin/boq-items/${id}`, {
    method: 'PATCH',
    body: payload,
    auth: true,
  })

// DELETE /admin/boq-items/{id}
export const deleteBoqItem = id =>
  apiRequest(`/admin/boq-items/${id}`, { method: 'DELETE', auth: true }) 
