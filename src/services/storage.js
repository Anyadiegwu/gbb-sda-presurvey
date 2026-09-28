// storage.js
// -----------------------------------------------------------------------------
// Small persistence layer for the prototype.
//
// There is no backend/database yet, so estimates are stored in browser
// localStorage under the key `gbb_estimates`.
//
// Production architecture should eventually replace these functions with API
// calls, while allowing the React components to keep a similar interface.
// -----------------------------------------------------------------------------

// Create a human-readable estimate reference such as:
// GBB-2026-483921
export function generateReference() {
  const year = new Date().getFullYear()

  // Generate a six-digit random number.
  const rand = Math.floor(
    100000 + Math.random() * 900000,
  )
    .toString()
    .slice(0, 6)

  return `GBB-${year}-${rand}`
}

// Read all previously saved estimates.
export function getSavedEstimates() {
  try {
    const saved = localStorage.getItem('gbb_estimates')

    // If nothing has been stored yet, start with an empty array.
    return JSON.parse(saved || '[]')
  } catch {
    // Invalid/corrupt localStorage should not crash the application.
    return []
  }
}

// Add a new estimate to the beginning of the saved list.
export function saveEstimate(estimate) {
  const estimates = getSavedEstimates()

  // unshift() places the newest estimate at index 0.
  estimates.unshift(estimate)

  localStorage.setItem(
    'gbb_estimates',
    JSON.stringify(estimates),
  )
}
