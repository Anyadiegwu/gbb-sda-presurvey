// EstimateStep.jsx
// -----------------------------------------------------------------------------
// Step 3 of the estimator.
//
// This component is intentionally mostly presentational. The pricing
// calculation has already happened in App through calculateEstimate().
//
// It:
//   1. displays NRC rows
//   2. displays ARC rows
//   3. displays totals
//   4. creates a basic Excel BOQ when the user clicks Export to Excel
// -----------------------------------------------------------------------------

import * as XLSX from 'xlsx'
import { formatNaira, formatNairaWhole } from '../utils/format'

// Build an Excel workbook from the calculated estimate.
//
// The array-of-arrays structure (`aoa`) is convenient for a basic BOQ because
// each inner array represents one spreadsheet row.
function exportEstimateToExcel(calc) {
  const rows = [
    ['S/N', 'Item Description', 'QTY', 'Rate', 'NRC', 'ARC'],

    // Section heading for one-off charges.
    ['', 'One-Off', '', '', '', ''],

    // NRC rows place their amount in the NRC column.
    ...calc.nrcRows.map((row, index) => [
      index + 1,
      row.description,
      row.qty,
      Number(row.rate),
      Number(row.amount),
      '',
    ]),

    // Section heading for recurring charges.
    ['', 'Recurring', '', '', '', ''],

    // ARC rows place their amount in the ARC column.
    ...calc.arcRows.map((row, index) => [
      calc.nrcRows.length + index + 1,
      row.description,
      row.qty,
      Number(row.rate),
      '',
      Number(row.amount),
    ]),

    // Totals.
    ['', 'Total NRC', '', '', Number(calc.totalNRC), ''],
    ['', 'Total ARC', '', '', '', Number(calc.totalARC)],
    ['', 'Grand Total (NRC + ARC)', '', '', '', Number(calc.grandTotal)],
  ]

  // Convert the JavaScript array into a SheetJS worksheet.
  const ws = XLSX.utils.aoa_to_sheet(rows)

  // Basic column widths so the exported BOQ is readable.
  ws['!cols'] = [
    { wch: 8 },
    { wch: 48 },
    { wch: 10 },
    { wch: 16 },
    { wch: 16 },
    { wch: 16 },
  ]

  // Create a new workbook and add the BOQ worksheet.
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'BOQ')

  // Ask SheetJS to create/download the Excel file.
  XLSX.writeFile(
    wb,
    `GBB-BOQ-${new Date().toISOString().slice(0, 10)}.xlsx`,
  )
}

// Reusable table-row component.
//
// `recurring` only changes the empty-state message; the row rendering itself
// is the same for NRC and ARC.
function Rows({ rows, recurring }) {
  if (!rows.length) {
    return (
      <tr>
        <td colSpan="4" className="muted">
          No {recurring ? 'recurring' : 'non-recurring'} charges.
        </td>
      </tr>
    )
  }

  return rows.map(row => (
    <tr key={`${row.description}-${row.amount}`}>
      <td>{row.description}</td>
      <td>{row.qty}</td>
      <td>
        {formatNairaWhole(row.rate)}
        {row.unit === 'm'
          ? '/m'
          : row.unit === 'Mbps'
            ? '/Mbps'
            : ''}
      </td>
      <td>{formatNairaWhole(row.amount)}</td>
    </tr>
  ))
}

export default function EstimateStep({ calc, onBack, onContinue }) {
  return (
    <section className="step-panel">
      <div className="card">
        <h1>Your Estimated Cost</h1>
        <p className="muted">
          Preliminary estimate based on the information provided.
        </p>

        <h3 style={{ marginTop: 20 }}>
          Non-Recurring Charges (NRC)
        </h3>

        <div className="table-wrap">
          <table className="estimate-table">
            <thead>
              <tr>
                <th>Item Description</th>
                <th>QTY</th>
                <th>Rate (₦)</th>
                <th>NRC (₦)</th>
              </tr>
            </thead>

            <tbody>
              <Rows rows={calc.nrcRows} />
            </tbody>
          </table>
        </div>

        <h3 style={{ marginTop: 20 }}>
          Annual Recurring Charges (ARC)
        </h3>

        <div className="table-wrap">
          <table className="estimate-table">
            <thead>
              <tr>
                <th>Item Description</th>
                <th>QTY</th>
                <th>Rate (₦)</th>
                <th>ARC (₦)</th>
              </tr>
            </thead>

            <tbody>
              <Rows rows={calc.arcRows} recurring />
            </tbody>
          </table>
        </div>

        <div className="summary-grid">
          <div className="summary-box">
            <div className="label">TOTAL NRC</div>
            <div className="amount">
              {formatNaira(calc.totalNRC)}
            </div>
          </div>

          <div className="summary-box">
            <div className="label">TOTAL ARC (Monthly)</div>
            <div className="amount">
              {formatNaira(calc.totalARC)}
            </div>
          </div>

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

        <div
          className="step-actions"
          style={{ gap: 10, flexWrap: 'wrap' }}
        >
          <button
            className="btn btn-text"
            type="button"
            onClick={onBack}
          >
            ← Back
          </button>

          <div
            style={{
              display: 'flex',
              gap: 10,
              flexWrap: 'wrap',
              marginLeft: 'auto',
            }}
          >
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => exportEstimateToExcel(calc)}
            >
              Export to Excel
            </button>

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
