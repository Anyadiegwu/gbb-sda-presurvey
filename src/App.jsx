// App.jsx
// -----------------------------------------------------------------------------
// This is the top-level React component for the Fibre Estimator.
//
// Think of App as the "orchestrator" of the application. It owns the main
// estimate draft and the current step, then passes the relevant data/functions
// down to the smaller step components.
//
// Data flow:
//
//   App state
//      ↓
//   LocationStep  → location + distance
//      ↓
//   RequirementsStep → bandwidth + rack choice
//      ↓
//   calculateEstimate() → pricing calculation
//      ↓
//   EstimateStep → displays/export estimate
//      ↓
//   SubmitStep → saves the completed request
// -----------------------------------------------------------------------------

import { useMemo, useState } from 'react'
import Stepper from './components/Stepper'
import LocationStep from './components/LocationStep'
import RequirementsStep from './components/RequirementsStep'
import EstimateStep from './components/EstimateStep'
import SubmitStep from './components/SubmitStep'
import { calculateEstimate } from './services/pricing'

// This object represents the information collected during the estimate.
// It lives in App so all four steps can access the same draft.
const initialDraft = {
  lat: null,
  lng: null,
  distanceMetres: null,
  nearestPopName: null,
  bandwidth: '20 Mbps',
  customMbps: null,
  providesOwnRack: false,
}

export default function App() {
  // `step` controls which screen is currently displayed.
  // React re-renders App whenever setStep() is called.
  const [step, setStep] = useState(1)

  // `draft` is the shared form state for the whole estimate.
  // Child components update it through setDraft.
  const [draft, setDraft] = useState(initialDraft)

  // useMemo prevents the pricing calculation from being repeated on every
  // render when the draft has not changed.
  //
  // The calculation is only possible after a valid distance has been selected.
  const calculation = useMemo(() => {
    if (!Number.isFinite(draft.distanceMetres)) return null
    return calculateEstimate(draft)
  }, [draft])

  // All four steps use this helper to move between screens.
  // Scrolling to the top makes a step change feel like a new page.
  const goToStep = nextStep => {
    setStep(nextStep)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <>
      {/* Accessibility link: keyboard users can skip directly to the main content. */}
      <a href="#main-content" className="skip-link">Skip to content</a>

      <div className="app-shell">
        <main className="workspace" id="main-content">
          {/* The stepper receives the current step so it can show progress. */}
          <Stepper currentStep={step} />

          {/* Step 1: choose the customer's site location. */}
          {step === 1 && (
            <LocationStep
              draft={draft}
              setDraft={setDraft}
              onContinue={() => goToStep(2)}
            />
          )}

          {/* Step 2: choose bandwidth and rack requirements. */}
          {step === 2 && (
            <RequirementsStep
              draft={draft}
              setDraft={setDraft}
              onBack={() => goToStep(1)}
              onContinue={() => goToStep(3)}
            />
          )}

          {/* Step 3: show the calculated BOQ/estimate. */}
          {step === 3 && calculation && (
            <EstimateStep
              calc={calculation}
              onBack={() => goToStep(2)}
              onContinue={() => goToStep(4)}
            />
          )}

          {/* Step 4: collect customer information and save the request. */}
          {step === 4 && calculation && (
            <SubmitStep
              draft={draft}
              calc={calculation}
              onBack={() => goToStep(3)}
            />
          )}
        </main>
      </div>
    </>
  )
}
