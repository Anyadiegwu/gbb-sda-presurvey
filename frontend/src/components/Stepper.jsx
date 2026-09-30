// Stepper.jsx
// -----------------------------------------------------------------------------
// Displays the four stages of the estimator.
// `currentStep` comes from App as a prop.
//
// This component does not own the step state. It only receives the current
// value and turns it into visual feedback.
// -----------------------------------------------------------------------------

export default function Stepper({ currentStep }) {
  // Keeping the labels in an array lets us generate the UI with .map()
  // instead of manually writing four almost-identical blocks.
  const steps = ['Location', 'Requirements', 'Estimate', 'Submit Request']

  return (
    <div className="stepper" aria-label="Estimate progress">
      {steps.map((label, index) => {
        // Arrays are zero-indexed, but our UI steps start at 1.
        const step = index + 1

        return (
          <div
            key={label}
            className={`step-item ${step === currentStep ? 'active' : ''} ${step < currentStep ? 'completed' : ''}`}
            data-step={step}
          >
            <div className="step-circle">{step}</div>
            <div className="step-label">{label}</div>
          </div>
        )
      })}
    </div>
  )
}
