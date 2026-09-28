// main.jsx
// -----------------------------------------------------------------------------
// This is the entry point of the React application.
//
// The browser loads index.html first. index.html contains <div id="root">.
// React then uses that element as the mounting point for the entire app:
//
//   index.html
//       ↓
//   main.jsx
//       ↓
//   <App />
//
// ReactDOM.createRoot() connects React's rendering system to the real DOM.
// -----------------------------------------------------------------------------

import React from 'react'
import ReactDOM from 'react-dom/client'

// Leaflet's CSS is required for the map controls, markers and map layout.
import 'leaflet/dist/leaflet.css'

// Global application styles.
import './styles/style.css'
import './styles/responsive.css'

// The root React component.
import App from './App'

// Find <div id="root"> in index.html and tell React to render App inside it.
//
// StrictMode is a development-time helper from React. It can intentionally
// run certain logic more than once in development to expose unsafe side
// effects. It does not represent two separate applications in production.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
