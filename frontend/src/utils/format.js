// format.js
// -----------------------------------------------------------------------------
// Presentation helpers for Nigerian Naira.
//
// Keeping formatting in one utility avoids duplicating the same
// toLocaleString() configuration throughout the React components.
// -----------------------------------------------------------------------------

// Format with two decimal places.
// Example: 2500000 → ₦2,500,000.00
export function formatNaira(amount) {
  const n = Number(amount) || 0

  return (
    '₦' +
    n.toLocaleString('en-NG', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  )
}

// Format without decimal places.
// Example: 2500000 → ₦2,500,000
export function formatNairaWhole(amount) {
  const n = Number(amount) || 0

  return (
    '₦' +
    n.toLocaleString('en-NG', {
      maximumFractionDigits: 0,
    })
  )
}
