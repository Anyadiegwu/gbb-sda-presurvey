// pricing.js
// -----------------------------------------------------------------------------
// This file is the application's pricing/calculation engine.
//
// It deliberately contains business logic rather than UI code.
//
// Main responsibilities:
//   - define fallback/default prices
//   - load admin pricing from localStorage
//   - preserve compatibility with the older bandwidth pricing structure
//   - convert bandwidth labels to Mbps
//   - calculate fibre, rack, router and bandwidth costs
//   - separate One-Off items (NRC) from Recurring items (ARC)
//
// The key formulae are:
//
//   Fibre cost    = distance in metres × fibre rate per metre
//   Bandwidth    = bandwidth in Mbps × admin rate per Mbps
//   Total NRC    = sum of one-off rows
//   Total ARC    = sum of recurring rows
//   Grand Total  = Total NRC + Total ARC
// -----------------------------------------------------------------------------

export const DEFAULT_PRICING = {
  items: {
    fibre: {
      description: "Fiber last mile to customer's site",
      rate: 4000,
      type: 'One-Off',
      unit: 'm',
    },
    rack: {
      description: '12U Rack (customer can provide)',
      rate: 195000,
      type: 'One-Off',
      unit: 'each',
    },
    router: {
      description: 'Huawei AR611W Router - Lease',
      rate: 262500,
      type: 'Recurring',
      unit: 'each',
    },
    bandwidth: {
      description: 'Internet bandwidth service',
      type: 'Recurring',
      ratePerMbps: 25000,
      unit: 'Mbps',
    },
  },
}

// JSON cloning creates a new object instead of returning the same reference.
// That prevents callers from accidentally mutating DEFAULT_PRICING.
const clone = value => JSON.parse(JSON.stringify(value))

// Load the active pricing configuration.
//
// localStorage is being used as the prototype's "database" for pricing.
// In the production application this should eventually come from a backend.
export function getPricingConfig() {
  try {
    const saved = JSON.parse(
      localStorage.getItem('gbb_pricing') || 'null',
    )

    // If the browser has no saved configuration, use defaults.
    if (!saved?.items) return clone(DEFAULT_PRICING)

    // Start from defaults so missing fields still have safe values.
    const merged = clone(DEFAULT_PRICING)

    // Override each known item with values supplied by the admin.
    Object.assign(
      merged.items.fibre,
      saved.items.fibre || {},
    )

    Object.assign(
      merged.items.rack,
      saved.items.rack || {},
    )

    Object.assign(
      merged.items.router,
      saved.items.router || {},
    )

    Object.assign(
      merged.items.bandwidth,
      saved.items.bandwidth || {},
    )

    // Older versions stored a bandwidth "Custom" option.
    // The current model uses one ratePerMbps value instead.
    const savedBandwidth = saved.items.bandwidth || {}

    if (savedBandwidth.ratePerMbps != null) {
      merged.items.bandwidth.ratePerMbps =
        Number(savedBandwidth.ratePerMbps) || 0
    } else if (savedBandwidth.options?.Custom != null) {
      merged.items.bandwidth.ratePerMbps =
        Number(savedBandwidth.options.Custom) || 0
    }

    // Do not keep the obsolete structure in the active configuration.
    delete merged.items.bandwidth.options

    return merged
  } catch (error) {
    // Bad JSON or unexpected localStorage data should not crash the app.
    console.error(
      'Unable to load GBB pricing configuration:',
      error,
    )

    return clone(DEFAULT_PRICING)
  }
}

// Persist a pricing configuration in the browser.
export function savePricingConfig(config) {
  localStorage.setItem(
    'gbb_pricing',
    JSON.stringify(config),
  )
}

// Convert a customer-facing bandwidth label into a numeric Mbps value.
//
// Examples:
//   "10 Mbps" → 10
//   "500 Mbps" → 500
//   "1 Gbps" → 1000
export function bandwidthToMbps(bandwidth) {
  if (!bandwidth) return 0

  const value = String(bandwidth).trim().toLowerCase()

  // Remove units and leave the numeric portion.
  const numericValue = parseFloat(
    value.replace(/[^0-9.]/g, ''),
  )

  if (!Number.isFinite(numericValue)) return 0

  // Gbps must be converted because the pricing rate is per Mbps.
  return value.includes('gbps')
    ? numericValue * 1000
    : numericValue
}

// Calculate a complete estimate from the current draft.
//
// `draft` comes from App and contains user selections such as distance,
// bandwidth and rack ownership.
export function calculateEstimate(draft) {
  const config = getPricingConfig()

  // Convert values from form/localStorage data to numbers defensively.
  const distanceMetres =
    Number(draft.distanceMetres) || 0

  const fibreRate =
    Number(config.items.fibre.rate) || 0

  const rackRate =
    Number(config.items.rack.rate) || 0

  const routerRate =
    Number(config.items.router.rate) || 0

  const bandwidthRatePerMbps =
    Number(config.items.bandwidth.ratePerMbps) || 0

  // Fibre formula:
  // distance (m) × rate per metre.
  const fibreCost = Math.round(
    distanceMetres * fibreRate,
  )

  // If the customer supplies the rack, there is no rack charge.
  const rackCost = draft.providesOwnRack
    ? 0
    : rackRate

  let bandwidthMbps = 0
  let bandwidthLabel = draft.bandwidth || ''

  // Custom bandwidth is already stored as a numeric Mbps value.
  if (draft.bandwidth === 'Custom') {
    bandwidthMbps = Number(draft.customMbps) || 0
    bandwidthLabel = `Custom (${bandwidthMbps} Mbps)`
  } else {
    // Preset labels such as "1 Gbps" are converted here.
    bandwidthMbps = bandwidthToMbps(draft.bandwidth)
  }

  // Bandwidth formula:
  // Mbps × admin price per Mbps.
  const bandwidthCost = Math.round(
    bandwidthMbps * bandwidthRatePerMbps,
  )

  // These arrays become the two sections of the BOQ.
  const nrcRows = []
  const arcRows = []

  // Helper that creates a consistent BOQ row and puts it into the
  // appropriate section based on the item's type.
  const addRow = (
    item,
    quantity,
    amount,
    rateOverride,
  ) => {
    if (!item) return

    const row = {
      description: item.description || '',
      qty: Number(quantity) || 0,

      // Some rows, such as bandwidth, need an explicit rate override.
      rate:
        rateOverride !== undefined
          ? Number(rateOverride) || 0
          : Number(item.rate) || 0,

      amount: Number(amount) || 0,

      // Only the exact value "Recurring" is treated as ARC.
      // Everything else defaults to One-Off/NRC.
      type:
        item.type === 'Recurring'
          ? 'Recurring'
          : 'One-Off',

      unit: item.unit || 'each',
    }

    if (row.type === 'Recurring') {
      arcRows.push(row)
    } else {
      nrcRows.push(row)
    }
  }

  // Add fibre only when there is a positive distance.
  if (distanceMetres > 0) {
    addRow(
      config.items.fibre,
      distanceMetres,
      fibreCost,
      fibreRate,
    )
  }

  // Add the rack only when GBB is providing it.
  if (!draft.providesOwnRack) {
    addRow(
      config.items.rack,
      1,
      rackCost,
      rackRate,
    )
  }

  // The router is always included in the current prototype.
  addRow(
    config.items.router,
    1,
    routerRate,
    routerRate,
  )

  // Bandwidth is represented as its own generated item because its
  // description depends on the customer's selected bandwidth.
  addRow(
    {
      description: bandwidthLabel,
      rate: bandwidthRatePerMbps,
      type:
        config.items.bandwidth.type || 'Recurring',
      unit: 'Mbps',
    },
    bandwidthMbps,
    bandwidthCost,
    bandwidthRatePerMbps,
  )

  // Sum all one-off amounts.
  const totalNRC = nrcRows.reduce(
    (sum, row) => sum + row.amount,
    0,
  )

  // Sum all recurring amounts.
  const totalARC = arcRows.reduce(
    (sum, row) => sum + row.amount,
    0,
  )

  return {
    distanceMetres,
    fibreCost,
    rackCost,
    routerLeaseCost: routerRate,
    bandwidthMbps,
    bandwidthCost,
    bandwidthLabel,
    bandwidthRatePerMbps,

    // Full BOQ sections.
    nrcRows,
    arcRows,

    // Totals.
    totalNRC,
    totalARC,
    grandTotal: totalNRC + totalARC,

    // Store the pricing used for this estimate. This is useful because an
    // estimate should retain the rates that were active when it was created.
    pricingSnapshot: clone(config),
  }
}
