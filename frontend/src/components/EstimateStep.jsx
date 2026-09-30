// EstimateStep.jsx
// -----------------------------------------------------------------------------
// Step 3 of the estimator.
//
// This component is responsible for displaying the calculated estimate
// to the customer.
//
// IMPORTANT:
// The actual pricing calculation happens in App through calculateEstimate().
// This component only displays the results.
//
// Customers see:
//   1. Item description
//   2. Quantity (QTY)
//   3. NRC amount OR ARC amount
//   4. Total NRC
//   5. Total ARC
//   6. Grand Total
//
// The internal pricing rates are NOT displayed to customers.
// -----------------------------------------------------------------------------

import { formatNaira, formatNairaWhole } from '../utils/format'


// -----------------------------------------------------------------------------
// Format quantity values for customer display.
// -----------------------------------------------------------------------------
//
// The pricing engine may calculate a value with many decimal places.
//
// Example:
//     7827.587381792852
//
// We don't want the customer to see all those decimal places.
//
// So we display:
//     7,827.59
//
// However, if the quantity is a whole number, such as 1 or 20,
// we display it without unnecessary decimal places.
//
// Examples:
//     1       → 1
//     20      → 20
//     7827.5  → 7,827.5
//     7827.58 → 7,827.58
//
// The original value is NOT changed. This is only for display.
// -----------------------------------------------------------------------------

function formatQuantity(value) {
  const number = Number(value)

  // If the value is not a valid number, just display it as it is.
  if (!Number.isFinite(number)) {
    return value
  }

  return number.toLocaleString('en-NG', {
    maximumFractionDigits: 2,
  })
}


// -----------------------------------------------------------------------------
// Reusable table-row component.
// -----------------------------------------------------------------------------
//
// `recurring` tells the component whether these rows belong to ARC.
//
// The table has only THREE columns now:
//
//     Item Description | QTY | NRC/ARC
//
// The pricing RATE is intentionally not displayed to customers.
// -----------------------------------------------------------------------------

function Rows({ rows, recurring }) {
  // If there are no rows, show a helpful message instead.
  if (!rows.length) {
    return (
      <tr>
        <td colSpan="3" className="muted">
          No {recurring ? 'recurring' : 'non-recurring'} charges.
        </td>
      </tr>
    )
  }

  return rows.map(row => (
    <tr key={`${row.description}-${row.amount}`}>
      {/* Item description */}
      <td>{row.description}</td>

      {/* Quantity */}
      <td>{formatQuantity(row.qty)}</td>

      {/* NRC or ARC amount */}
      <td>{formatNairaWhole(row.amount)}</td>
    </tr>
  ))
}


// -----------------------------------------------------------------------------
// Main EstimateStep component.
// -----------------------------------------------------------------------------

export default function EstimateStep({ calc, onBack, onContinue }) {
  return (
    <section className="step-panel">
      <div className="card">

        {/* -------------------------------------------------------------------
            Page heading
        ------------------------------------------------------------------- */}

        <h1>Your Estimated Cost</h1>

        <p className="muted">
          Preliminary estimate based on the information provided.
        </p>


        {/* ===================================================================
            NON-RECURRING CHARGES
        =================================================================== */}

        <h3 style={{ marginTop: 20 }}>
          Non-Recurring Charges (NRC)
        </h3>

        <div className="table-wrap">
          <table className="estimate-table">

            <thead>
              <tr>
                <th>Item Description</th>
                <th>QTY</th>
                <th>NRC (₦)</th>
              </tr>
            </thead>

            <tbody>
              <Rows rows={calc.nrcRows} />
            </tbody>

          </table>
        </div>


        {/* ===================================================================
            ANNUAL RECURRING CHARGES
        =================================================================== */}

        <h3 style={{ marginTop: 20 }}>
          Annual Recurring Charges (ARC)
        </h3>

        <div className="table-wrap">
          <table className="estimate-table">

            <thead>
              <tr>
                <th>Item Description</th>
                <th>QTY</th>
                <th>ARC (₦)</th>
              </tr>
            </thead>

            <tbody>
              <Rows rows={calc.arcRows} recurring />
            </tbody>

          </table>
        </div>


        {/* ===================================================================
            ESTIMATE SUMMARY
        =================================================================== */}

        <div className="summary-grid">

          {/* Total NRC */}
          <div className="summary-box">
            <div className="label">
              TOTAL NRC
            </div>

            <div className="amount">
              {formatNaira(calc.totalNRC)}
            </div>
          </div>


          {/* Total ARC */}
          <div className="summary-box">
            <div className="label">
              TOTAL ARC (Monthly)
            </div>

            <div className="amount">
              {formatNaira(calc.totalARC)}
            </div>
          </div>


          {/* Grand Total */}
          <div
            className="summary-box"
            style={{ gridColumn: '1/-1' }}
          >
            <div className="label">
              GRAND TOTAL (NRC + ARC)
            </div>

            <div className="amount">
              {formatNaira(calc.grandTotal)}
            </div>
          </div>

        </div>


        {/* ===================================================================
            STEP ACTIONS
        =================================================================== */}

        <div
          className="step-actions"
          style={{ gap: 10, flexWrap: 'wrap' }}
        >

          {/* Back button */}
          <button
            className="btn btn-text"
            type="button"
            onClick={onBack}
          >
            ← Back
          </button>


          {/* Right-side actions */}
          <div
            style={{
              display: 'flex',
              gap: 10,
              flexWrap: 'wrap',
              marginLeft: 'auto',
            }}
          >

            {/* Continue to Submit step */}
            <button
              className="btn btn-primary"
              type="button"
              onClick={onContinue}
            >
              Continue →
            </button>

          </div>

        </div>

      </div>
    </section>
  )
}   