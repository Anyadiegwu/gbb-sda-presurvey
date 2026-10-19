// // App.jsx
// // -----------------------------------------------------------------------------
// // This is the top-level React component for the Fibre Estimator.
// //
// // App controls the customer estimator.
// //
// // The Admin page is handled separately based on the browser URL.
// // -----------------------------------------------------------------------------

// import { useMemo, useState } from 'react'

// import Stepper from './components/Stepper'
// import LocationStep from './components/LocationStep'
// import RequirementsStep from './components/RequirementsStep'
// import EstimateStep from './components/EstimateStep'
// import SubmitStep from './components/SubmitStep'

// import { calculateEstimate } from './services/pricing'

// import Admin from './pages/Admin'


// // -----------------------------------------------------------------------------
// // INITIAL ESTIMATE DATA
// // -----------------------------------------------------------------------------
// //
// // This object represents the information collected during the estimate.
// //
// // It lives in App because multiple child components need access to it.
// //
// const initialDraft = {
//   lat: null,
//   lng: null,
//   distanceMetres: null,
//   nearestPopName: null,

//   bandwidth: '20 Mbps',
//   customMbps: null,

//   providesOwnRack: false,
// }


// // -----------------------------------------------------------------------------
// // CUSTOMER ESTIMATOR
// // -----------------------------------------------------------------------------
// //
// // We put the estimator into its own component.
// //
// // This means the hooks below are always used correctly.
// // -----------------------------------------------------------------------------

// function Estimator() {

//   // Controls which step of the estimator is currently visible.
//   const [step, setStep] = useState(1)

//   // Shared estimate information.
//   const [draft, setDraft] = useState(initialDraft)


//   // ---------------------------------------------------------------------------
//   // CALCULATE ESTIMATE
//   // ---------------------------------------------------------------------------
//   //
//   // useMemo means React does not unnecessarily recalculate the estimate
//   // when unrelated things cause the component to render.
//   //
//   const calculation = useMemo(() => {

//     // We cannot calculate a fibre estimate without a distance.
//     if (!Number.isFinite(draft.distanceMetres)) {
//       return null
//     }

//     return calculateEstimate(draft)

//   }, [draft])


//   // ---------------------------------------------------------------------------
//   // MOVE BETWEEN STEPS
//   // ---------------------------------------------------------------------------

//   const goToStep = nextStep => {

//     setStep(nextStep)

//     // Scroll the page back to the top after changing steps.
//     window.scrollTo({
//       top: 0,
//       behavior: 'smooth',
//     })
//   }


//   // ---------------------------------------------------------------------------
//   // CUSTOMER ESTIMATOR UI
//   // ---------------------------------------------------------------------------

//   return (
//     <>
//       {/* Accessibility link for keyboard users. */}
//       <a
//         href="#main-content"
//         className="skip-link"
//       >
//         Skip to content
//       </a>


//       <div className="app-shell">

//         <main
//           className="workspace"
//           id="main-content"
//         >

//           {/* Shows Location → Requirements → Estimate → Submit */}
//           <Stepper currentStep={step} />


//           {/* ---------------------------------------------------------------
//               STEP 1
//               --------------------------------------------------------------- */}

//           {step === 1 && (
//             <LocationStep
//               draft={draft}
//               setDraft={setDraft}
//               onContinue={() => goToStep(2)}
//             />
//           )}


//           {/* ---------------------------------------------------------------
//               STEP 2
//               --------------------------------------------------------------- */}

//           {step === 2 && (
//             <RequirementsStep
//               draft={draft}
//               setDraft={setDraft}
//               onBack={() => goToStep(1)}
//               onContinue={() => goToStep(3)}
//             />
//           )}


//           {/* ---------------------------------------------------------------
//               STEP 3
//               --------------------------------------------------------------- */}

//           {step === 3 && calculation && (
//             <EstimateStep
//               calc={calculation}
//               onBack={() => goToStep(2)}
//               onContinue={() => goToStep(4)}
//             />
//           )}


//           {/* ---------------------------------------------------------------
//               STEP 4
//               --------------------------------------------------------------- */}

//           {step === 4 && calculation && (
//             <SubmitStep
//               draft={draft}
//               calc={calculation}
//               onBack={() => goToStep(3)}
//             />
//           )}

//         </main>

//       </div>
//     </>
//   )
// }


// // -----------------------------------------------------------------------------
// // APP
// // -----------------------------------------------------------------------------
// //
// // App decides which top-level page should be displayed.
// //
// // /admin → Admin dashboard
// // everything else → customer estimator
// // -----------------------------------------------------------------------------

// export default function App() {

//   const pathname = window.location.pathname


//   // Admin page.
//   if (pathname === '/gbb/admin') {
//     return <Admin />
//   }


//   // Customer estimator.
//   return <Estimator />
// }


// App.jsx
// -----------------------------------------------------------------------------
// Top-level React component for the Fibre Estimator.
//
// The customer estimator is a 4-step flow. Data now comes from the backend:
//   Step 1  LocationStep      → POST /quotes/resolve-location
//   Step 2  RequirementsStep  → (collects bandwidth / rack choice)
//   Step 3  EstimateStep      → POST /quotes/calculate
//   Step 4  SubmitStep        → POST /submissions/
//
// The Admin page is handled separately based on the browser URL.
// -----------------------------------------------------------------------------

import { useState } from 'react'

import Stepper from './components/Stepper'
import LocationStep from './components/LocationStep'
import RequirementsStep from './components/RequirementsStep'
import EstimateStep from './components/EstimateStep'
import SubmitStep from './components/SubmitStep'

import Admin from './pages/Admin'

// Information collected during the estimate. It lives in App because several
// child components need it.
const initialDraft = {
  // Filled by LocationStep from the backend's resolve-location response
  lat: null,
  lng: null,
  distanceMetres: null,
  manholeId: null,
  nearestPopName: null,

  // Chosen in RequirementsStep
  bandwidth: '20 Mbps',
  customMbps: null,
  providesOwnRack: false,
}

function Estimator() {
  const [step, setStep] = useState(1)
  const [draft, setDraft] = useState(initialDraft)

  // The priced quote returned by the backend. EstimateStep fetches it and
  // stores it here so SubmitStep can send it with the request.
  const [quote, setQuote] = useState(null)

  const goToStep = nextStep => {
    setStep(nextStep)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>

      <div className="app-shell">
        <main className="workspace" id="main-content">
          <Stepper currentStep={step} />

          {step === 1 && (
            <LocationStep
              draft={draft}
              setDraft={setDraft}
              onContinue={() => goToStep(2)}
            />
          )}

          {step === 2 && (
            <RequirementsStep
              draft={draft}
              setDraft={setDraft}
              onBack={() => goToStep(1)}
              onContinue={() => goToStep(3)}
            />
          )}

          {step === 3 && (
            <EstimateStep
              draft={draft}
              quote={quote}
              setQuote={setQuote}
              onBack={() => goToStep(2)}
              onContinue={() => goToStep(4)}
            />
          )}

          {step === 4 && quote && (
            <SubmitStep
              draft={draft}
              calc={quote}
              onBack={() => goToStep(3)}
            />
          )}
        </main>
      </div>
    </>
  )
}

// /gbb/admin → Admin dashboard, everything else → customer estimator
export default function App() {
  if (window.location.pathname === '/gbb/admin') {
    return <Admin />
  }

  return <Estimator />
}
