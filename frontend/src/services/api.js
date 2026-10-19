// api.js
// -----------------------------------------------------------------------------
// The single place that talks to the FastAPI backend.
//
// Every other service (location, pricing, submissions, admin) calls
// apiRequest() instead of using fetch() directly, so base URL, JSON handling,
// the admin token and error messages are handled once.
// -----------------------------------------------------------------------------

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/$/, '')

const TOKEN_KEY = 'gbb_admin_token'

// The admin JWT lives in sessionStorage so it is cleared when the tab closes.
export const getToken = () => {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export const setToken = token => sessionStorage.setItem(TOKEN_KEY, token)

export const clearToken = () => {
  try {
    sessionStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}

// Error type thrown for every failed request.
// `status` is the HTTP status (0 = the server could not be reached).
export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI sends errors as { detail: "text" } or, for validation errors (422),
// { detail: [{ loc: [...], msg: "..." }] }. Turn both into one readable string.
function extractMessage(data, fallback) {
  const detail = data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        const field = Array.isArray(item.loc)
          ? item.loc.filter(part => part !== 'body').join('.')
          : ''
        return field ? `${field}: ${item.msg}` : item.msg
      })
      .join('; ')
  }

  return fallback
}

// path    - e.g. '/quotes/calculate'
// options - { method, body, auth, signal }
//             body: plain object (sent as JSON) or FormData (sent as multipart)
//             auth: true attaches the admin Bearer token
export async function apiRequest(
  path,
  { method = 'GET', body, auth = false, signal } = {},
) {
  const headers = { Accept: 'application/json' }

  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  let payload
  if (body instanceof FormData) {
    payload = body // the browser sets the multipart boundary itself
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: payload,
      signal,
    })
  } catch (error) {
    // Aborted requests are intentional; let the caller handle them.
    if (error.name === 'AbortError') throw error

    throw new ApiError(
      'Cannot reach the server. Please check your connection and try again.',
      0,
    )
  }

  let data = null
  try {
    data = await response.json()
  } catch {
    /* empty or non-JSON body */
  }

  if (!response.ok) {
    throw new ApiError(
      extractMessage(data, `Request failed (${response.status})`),
      response.status,
    )
  }

  return data
}
