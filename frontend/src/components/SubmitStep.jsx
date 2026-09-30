// SubmitStep.jsx
// -----------------------------------------------------------------------------
// Step 4 of the estimator.
//
// This component handles the final customer form. It performs client-side
// validation, creates a reference number, builds the final estimate object,
// and saves that object through services/storage.js.
//
// NOTE: saveEstimate() currently writes to browser localStorage. This is a
// frontend prototype, not a real backend submission system.
// -----------------------------------------------------------------------------

import { useState } from 'react'
import { formatNaira } from '../utils/format'
import { generateReference, saveEstimate } from '../services/storage'

// Return an object containing validation errors.
// An empty object means the form passed validation.
function validate(form) {
  const errors = {}

  if (!form.fullName.trim()) {
    errors.fullName = 'Please enter your full name.'
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = 'Please enter a valid email address.'
  }

  if (!form.phone.trim()) {
    errors.phone = 'Please enter your phone number.'
  }

  if (!form.siteAddress.trim()) {
    errors.siteAddress = 'Please enter the site address.'
  }

  return errors
}

export default function SubmitStep({ draft, calc, onBack }) {
  // Form state belongs to this component because these fields are only needed
  // during the final submission step.
  const [form, setForm] = useState({
    fullName: '',
    company: '',
    email: '',
    phone: '',
    siteAddress: '',
    notes: '',
  })

  // Stores validation messages by field name.
  const [errors, setErrors] = useState({})

  // Once the request is saved, this contains the saved estimate.
  const [submitted, setSubmitted] = useState(null)

  // Used to disable the submit button during the simulated submission delay.
  const [submitting, setSubmitting] = useState(false)

  // Generic helper for updating one field without replacing the rest of
  // the form object.
  const update = (key, value) =>
    setForm(current => ({
      ...current,
      [key]: value,
    }))

  const submit = event => {
    // Prevent the browser from performing its normal full-page form submit.
    event.preventDefault()

    const nextErrors = validate(form)
    setErrors(nextErrors)

    // Stop here if at least one validation error exists.
    if (Object.keys(nextErrors).length) return

    setSubmitting(true)

    // This timeout simulates a network request. In a production application,
    // this is where an API call to the backend would happen.
    setTimeout(() => {
      const reference = generateReference()

      // Build one complete record containing customer, location,
      // requirements and calculated pricing.
      const estimate = {
        reference,

        date: new Date().toLocaleDateString('en-NG', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        }),

        status: 'Pending Review',

        customer: { ...form },

        location: {
          lat: draft.lat,
          lng: draft.lng,
          distanceMetres: draft.distanceMetres,
          nearestPopName: draft.nearestPopName,
        },

        requirements: {
          bandwidthLabel: calc.bandwidthLabel,
          bandwidthMbps: calc.bandwidthMbps,
          providesOwnRack: draft.providesOwnRack,
        },

        calc,
      }

      // Save the completed record locally.
      saveEstimate(estimate)

      // Switching submitted from null to the estimate causes React to render
      // the success screen below.
      setSubmitted(estimate)
      setSubmitting(false)
    }, 900)
  }

  // After successful submission, show the confirmation view instead of
  // displaying the form again.
  if (submitted) {
    return (
      <section className="step-panel">
        <div className="card success-wrap">
          <div className="success-icon">
            <svg
              width="34"
              height="34"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <h1>Request submitted successfully.</h1>

          <p className="muted">
            Our team will be in touch within 24 hours to schedule
            your site survey.
          </p>

          <div className="reference-badge">
            {submitted.reference}
          </div>

          <div
            className="step-actions"
            style={{
              justifyContent: 'center',
              gap: 12,
              marginTop: 26,
            }}
          >
            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => window.print()}
            >
              Print / Save PDF
            </button>

            <button
              className="btn btn-primary"
              type="button"
              onClick={() => window.location.reload()}
            >
              New Estimate
            </button>
          </div>
        </div>
      </section>
    )
  }

  // Small helper that generates the repeated input markup for the simple
  // text fields. It demonstrates how functions can return JSX.
  const field = (
    key,
    label,
    type = 'text',
    required = true,
  ) => (
    <div className={`field ${errors[key] ? 'error' : ''}`}>
      <label htmlFor={key}>
        {label}
        {required ? ' *' : ''}
      </label>

      <input
        id={key}
        type={type}
        value={form[key]}
        onChange={e => update(key, e.target.value)}
      />

      {errors[key] && (
        <div className="field-error-msg">
          {errors[key]}
        </div>
      )}
    </div>
  )

  return (
    <section className="step-panel">
      <div className="card">
        <div className="icon-circle">
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </div>

        <h1>What's next?</h1>

        <p className="muted">
          To receive an official proposal and schedule a detailed
          site survey, please submit your request.
        </p>

        <ul className="checklist">
          <li>✓ Our team will review your request</li>
          <li>✓ We'll contact you within 24 hours</li>
          <li>✓ Site survey will be scheduled</li>
        </ul>

        <form onSubmit={submit} noValidate>
          <h3 style={{ marginTop: 8 }}>Your details</h3>

          {field('fullName', 'Full name')}
          {field(
            'company',
            'Company / Organization',
            'text',
            false,
          )}
          {field('email', 'Email', 'email')}
          {field('phone', 'Phone number', 'tel')}
          {field('siteAddress', 'Site address')}

          <div className="field">
            <label htmlFor="notes">Additional notes</label>

            <textarea
              id="notes"
              rows="3"
              value={form.notes}
              onChange={e => update('notes', e.target.value)}
            />
          </div>

          <h3 style={{ marginTop: 10 }}>Review your request</h3>

          <div className="review-section">
            <h3>Location</h3>

            <div className="review-row">
              <span>Coordinates</span>
              <span>
                {draft.lat.toFixed(5)}, {draft.lng.toFixed(5)}
              </span>
            </div>

            <div className="review-row">
              <span>Estimated fibre distance</span>
              <span>
                {(draft.distanceMetres / 1000).toFixed(2)} km
              </span>
            </div>
          </div>

          <div className="review-section">
            <h3>Requirements</h3>

            <div className="review-row">
              <span>Bandwidth</span>
              <span>{calc.bandwidthLabel}</span>
            </div>

            <div className="review-row">
              <span>Rack</span>
              <span>
                {draft.providesOwnRack
                  ? 'Customer-provided'
                  : 'GBB to provide 12U Rack'}
              </span>
            </div>
          </div>

          <div className="review-section">
            <h3>Estimate</h3>

            <div className="review-row">
              <span>Total NRC</span>
              <span>{formatNaira(calc.totalNRC)}</span>
            </div>

            <div className="review-row">
              <span>Total ARC (monthly)</span>
              <span>{formatNaira(calc.totalARC)}</span>
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
              type="submit"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <span className="spinner" />
                  Submitting...
                </>
              ) : (
                'Submit Request →'
              )}
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
