// RequirementsStep.jsx
// -----------------------------------------------------------------------------
// Step 2 of the estimator.
//
// This component collects the commercial/service requirements that affect
// the estimate:
//   - bandwidth
//   - whether GBB or the customer provides the 12U rack
//
// The actual prices come from services/pricing.js, so this component does not
// contain hard-coded commercial rates.
// -----------------------------------------------------------------------------

import { formatNairaWhole } from '../utils/format'
import { getPricingConfig } from '../services/pricing'

// These are customer-facing bandwidth choices.
// The pricing engine later converts the selected label into Mbps.
const bandwidths = [
  '10 Mbps',
  '20 Mbps',
  '50 Mbps',
  '100 Mbps',
  '200 Mbps',
  '500 Mbps',
  '1 Gbps',
  'Custom',
]

export default function RequirementsStep({
  draft,
  setDraft,
  onBack,
  onContinue,
}) {
  // Read the current rack price from the pricing configuration.
  // This means the UI automatically reflects an admin-configured rate.
  const rackRate = getPricingConfig().items.rack.rate

  // Custom bandwidth must be at least 1 Mbps.
  const customInvalid =
    draft.bandwidth === 'Custom' &&
    (!draft.customMbps || Number(draft.customMbps) < 1)

  return (
    <section className="step-panel">
      <div className="card">
        <h1>What service do you need?</h1>
        <p className="muted">
          Choose your bandwidth and equipment requirements
        </p>

        <div className="field" style={{ marginTop: 18 }}>
          <label>Bandwidth</label>

          <div className="pill-group">
            {bandwidths.map(value => (
              <button
                key={value}
                type="button"
                className={`pill ${
                  draft.bandwidth === value ? 'selected' : ''
                }`}
                onClick={() =>
                  setDraft(current => ({
                    ...current,
                    bandwidth: value,
                  }))
                }
              >
                {value}
              </button>
            ))}
          </div>

          {/* Only show the numeric input when Custom is selected. */}
          {draft.bandwidth === 'Custom' && (
            <div className="field" style={{ marginTop: 12 }}>
              <label htmlFor="custom-mbps">
                Custom bandwidth (Mbps)
              </label>

              <input
                type="number"
                id="custom-mbps"
                min="1"
                value={draft.customMbps || ''}
                onChange={e =>
                  setDraft(current => ({
                    ...current,
                    customMbps: e.target.value,
                  }))
                }
                placeholder="e.g. 750"
              />
            </div>
          )}
        </div>

        <div className="field">
          <label>Rack</label>

          <div className="select-card-grid">
            <div
              className={`select-card ${
                !draft.providesOwnRack ? 'selected' : ''
              }`}
              onClick={() =>
                setDraft(current => ({
                  ...current,
                  providesOwnRack: false,
                }))
              }
            >
              <svg
                className="check-icon"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>

              <h3>GBB to provide 12U Rack</h3>
              <p className="muted">
                {formatNairaWhole(rackRate)} one-off
              </p>
            </div>

            <div
              className={`select-card ${
                draft.providesOwnRack ? 'selected' : ''
              }`}
              onClick={() =>
                setDraft(current => ({
                  ...current,
                  providesOwnRack: true,
                }))
              }
            >
              <svg
                className="check-icon"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>

              <h3>I will provide my own rack</h3>
              <p className="muted">No additional charge</p>
            </div>
          </div>
        </div>

        <div className="step-actions">
          <button
            className="btn btn-text"
            type="button"
            onClick={onBack}
          >
            ← Back
          </button>

          <button
            className="btn btn-primary"
            type="button"
            onClick={() => !customInvalid && onContinue()}
            disabled={customInvalid}
          >
            Continue →
          </button>
        </div>
      </div>
    </section>
  )
}
