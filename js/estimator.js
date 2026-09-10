/* ============================================
   estimator.js
   GBB Fiber Estimator
   Pricing & Calculation Engine

   - Pricing is controlled from admin.html
   - One-Off items → NRC
   - Recurring items → ARC
   - Grand Total = NRC + ARC
   - Pricing is stored in localStorage

   BANDWIDTH PRICING:
   - Admin sets ONE price per Mbps
   - Selected bandwidth × price per Mbps
   - 1 Gbps = 1000 Mbps
   - Custom bandwidth uses the same calculation
   ============================================ */


/* ============================================
   DEFAULT PRICING
   ============================================ */

const DEFAULT_PRICING = {
  items: {

    fibre: {
      description: "Fiber last mile to customer's site",
      rate: 4000,
      type: "One-Off",
      unit: "m"
    },

    rack: {
      description: "12U Rack (customer can provide)",
      rate: 195000,
      type: "One-Off",
      unit: "each"
    },

    router: {
      description: "Huawei AR611W Router - Lease",
      rate: 262500,
      type: "Recurring",
      unit: "each"
    },

    bandwidth: {
      description: "Internet bandwidth service",
      type: "Recurring",
      ratePerMbps: 25000,
      unit: "Mbps"
    }
  }
};


/* ============================================
   HELPER FUNCTIONS
   ============================================ */

/**
 * Creates a completely independent copy
 * of the pricing configuration.
 */
function clonePricing(value) {
  return JSON.parse(JSON.stringify(value));
}


/**
 * Returns the current pricing configuration.
 *
 * If an admin has saved custom pricing,
 * that pricing is loaded from localStorage.
 *
 * Otherwise the default pricing is used.
 *
 * Also includes migration support for the
 * previous bandwidth pricing structure.
 */
function getPricingConfig() {

  try {

    const saved = JSON.parse(
      localStorage.getItem("gbb_pricing") || "null"
    );

    /* No saved admin pricing */
    if (!saved || !saved.items) {
      return clonePricing(DEFAULT_PRICING);
    }

    /* Start with defaults */
    const merged = clonePricing(DEFAULT_PRICING);


    /* ==========================================
       FIBRE
       ========================================== */

    Object.assign(
      merged.items.fibre,
      saved.items.fibre || {}
    );


    /* ==========================================
       RACK
       ========================================== */

    Object.assign(
      merged.items.rack,
      saved.items.rack || {}
    );


    /* ==========================================
       ROUTER
       ========================================== */

    Object.assign(
      merged.items.router,
      saved.items.router || {}
    );


    /* ==========================================
       BANDWIDTH
       ========================================== */

    const savedBandwidth =
      saved.items.bandwidth || {};

    Object.assign(
      merged.items.bandwidth,
      savedBandwidth
    );


    /*
       New system:

       bandwidth.ratePerMbps

       If the saved configuration does not
       contain it, try to migrate the old
       "Custom" bandwidth rate.
    */

    if (
      savedBandwidth.ratePerMbps !== undefined &&
      savedBandwidth.ratePerMbps !== null
    ) {

      merged.items.bandwidth.ratePerMbps =
        Number(savedBandwidth.ratePerMbps) || 0;

    } else if (
      savedBandwidth.options &&
      savedBandwidth.options.Custom !== undefined
    ) {

      /*
         Migration from the old pricing system.

         The previous Custom rate was already
         intended to represent a price per Mbps,
         so it can safely become ratePerMbps.
      */

      merged.items.bandwidth.ratePerMbps =
        Number(savedBandwidth.options.Custom) || 0;
    }

    /*
       Remove the old options object from the
       active configuration so the application
       consistently uses ratePerMbps.
    */

    delete merged.items.bandwidth.options;


    return merged;

  } catch (error) {

    console.error(
      "Unable to load GBB pricing configuration:",
      error
    );

    return clonePricing(DEFAULT_PRICING);
  }
}


/**
 * Saves a pricing configuration.
 */
function savePricingConfig(config) {

  try {

    localStorage.setItem(
      "gbb_pricing",
      JSON.stringify(config)
    );

    return true;

  } catch (error) {

    console.error(
      "Unable to save GBB pricing configuration:",
      error
    );

    return false;
  }
}


/**
 * Resets pricing back to the default configuration.
 */
function resetPricingConfig() {

  localStorage.removeItem("gbb_pricing");
}


/* ============================================
   COMPATIBILITY PRICING OBJECT
   ============================================ */

/*
   Keeps older frontend/PDF/export code working.

   Bandwidth now exposes:
   pricing.bandwidthRatePerMbps
*/

function getPricingCompatibility() {

  const config = getPricingConfig();

  return {

    fibrePerMeter:
      Number(config.items.fibre.rate) || 0,

    rack12U:
      Number(config.items.rack.rate) || 0,

    routerLease:
      Number(config.items.router.rate) || 0,

    bandwidthRatePerMbps:
      Number(
        config.items.bandwidth.ratePerMbps
      ) || 0
  };
}


/*
   Dynamic pricing object.
*/

const pricing = new Proxy(
  {},

  {
    get(target, property) {

      return getPricingCompatibility()[property];
    }
  }
);


/* ============================================
   BANDWIDTH HELPERS
   ============================================ */

/**
 * Converts a bandwidth label to Mbps.
 *
 * Examples:
 *
 * "10 Mbps"  → 10
 * "500 Mbps" → 500
 * "1 Gbps"   → 1000
 */
function bandwidthToMbps(bandwidth) {

  if (!bandwidth) {
    return 0;
  }

  const value = String(bandwidth)
    .trim()
    .toLowerCase();

  const numericValue =
    parseFloat(value.replace(/[^0-9.]/g, ""));

  if (!Number.isFinite(numericValue)) {
    return 0;
  }

  if (value.includes("gbps")) {
    return numericValue * 1000;
  }

  return numericValue;
}


/**
 * Calculates the price for a bandwidth.
 *
 * Formula:
 *
 * Mbps × Admin price per Mbps
 *
 * Example:
 *
 * 100 Mbps × ₦25,000 = ₦2,500,000
 */
function estimateBandwidthCost(mbps) {

  const config = getPricingConfig();

  const ratePerMbps =
    Number(
      config.items.bandwidth.ratePerMbps
    ) || 0;

  const bandwidth =
    Number(mbps) || 0;

  return Math.round(
    bandwidth * ratePerMbps
  );
}


/**
 * Calculates the price for custom bandwidth.
 */
function estimateCustomBandwidthCost(mbps) {

  return estimateBandwidthCost(mbps);
}


/* ============================================
   MAIN ESTIMATE CALCULATION
   ============================================ */

/**
 * Calculates the customer's estimate.
 *
 * draft should contain:
 *
 * {
 *   distanceMetres,
 *   bandwidth,
 *   customMbps,
 *   providesOwnRack
 * }
 *
 * Returns:
 *
 * {
 *   nrcRows,
 *   arcRows,
 *   totalNRC,
 *   totalARC,
 *   grandTotal,
 *   ...
 * }
 */
function calculateEstimate(draft) {

  const config = getPricingConfig();

  const distanceMetres =
    Number(draft.distanceMetres) || 0;


  /* ==========================================
     GET CURRENT RATES
     ========================================== */

  const fibreRate =
    Number(config.items.fibre.rate) || 0;

  const rackRate =
    Number(config.items.rack.rate) || 0;

  const routerRate =
    Number(config.items.router.rate) || 0;

  const bandwidthRatePerMbps =
    Number(
      config.items.bandwidth.ratePerMbps
    ) || 0;


  /* ==========================================
     FIBRE
     ========================================== */

  const fibreCost =
    Math.round(
      distanceMetres * fibreRate
    );


  /* ==========================================
     RACK
     ========================================== */

  let rackCost = 0;

  if (!draft.providesOwnRack) {

    rackCost = rackRate;
  }


  /* ==========================================
     BANDWIDTH
     ========================================== */

  let bandwidthMbps = 0;

  let bandwidthLabel =
    draft.bandwidth || "";


  if (draft.bandwidth === "Custom") {

    bandwidthMbps =
      Number(draft.customMbps) || 0;

    bandwidthLabel =
      `Custom (${bandwidthMbps} Mbps)`;

  } else {

    bandwidthMbps =
      bandwidthToMbps(draft.bandwidth);
  }


  const bandwidthCost =
    estimateBandwidthCost(
      bandwidthMbps
    );


  /* ==========================================
     NRC AND ARC ROWS
     ========================================== */

  const nrcRows = [];
  const arcRows = [];


  /**
   * Adds an item to the correct section.
   *
   * One-Off   → NRC
   * Recurring → ARC
   */
  function addRow(
    item,
    quantity,
    amount,
    rateOverride
  ) {

    if (!item) {
      return;
    }


    const qty =
      Number(quantity) || 0;

    const rate =
      rateOverride !== undefined
        ? Number(rateOverride) || 0
        : Number(item.rate) || 0;

    const total =
      Number(amount) || 0;


    const row = {

      description:
        item.description || "",

      qty: qty,

      rate: rate,

      amount: total,

      type:
        item.type === "Recurring"
          ? "Recurring"
          : "One-Off",

      unit:
        item.unit || "each"
    };


    if (row.type === "Recurring") {

      arcRows.push(row);

    } else {

      nrcRows.push(row);
    }
  }


  /* ==========================================
     ADD FIBRE
     ========================================== */

  if (distanceMetres > 0) {

    addRow(
      config.items.fibre,
      distanceMetres,
      fibreCost,
      fibreRate
    );
  }


  /* ==========================================
     ADD RACK
     ========================================== */

  if (!draft.providesOwnRack) {

    addRow(
      config.items.rack,
      1,
      rackCost,
      rackRate
    );
  }


  /* ==========================================
     ADD ROUTER
     ========================================== */

  addRow(
    config.items.router,
    1,
    routerRate,
    routerRate
  );


  /* ==========================================
     ADD BANDWIDTH
     ========================================== */

  const bandwidthItem = {

    description:
      bandwidthLabel,

    rate:
      bandwidthRatePerMbps,

    type:
      config.items.bandwidth.type ||
      "Recurring",

    unit:
      "Mbps"
  };


  /*
     IMPORTANT:

     QTY is now the actual bandwidth in Mbps.

     Example:

     50 Mbps
     QTY = 50
     Rate = ₦25,000
     ARC = ₦1,250,000
  */

  addRow(
    bandwidthItem,
    bandwidthMbps,
    bandwidthCost,
    bandwidthRatePerMbps
  );


  /* ==========================================
     CALCULATE TOTALS
     ========================================== */

  const totalNRC =
    nrcRows.reduce(
      (sum, row) => {

        return (
          sum +
          Number(row.amount || 0)
        );

      },
      0
    );


  const totalARC =
    arcRows.reduce(
      (sum, row) => {

        return (
          sum +
          Number(row.amount || 0)
        );

      },
      0
    );


  /*
     Grand Total:

     NRC + ARC
  */

  const grandTotal =
    totalNRC + totalARC;


  /* ==========================================
     RETURN COMPLETE RESULT
     ========================================== */

  return {

    distanceMetres,

    fibreCost,

    rackCost,

    routerLeaseCost:
      routerRate,

    bandwidthMbps,

    bandwidthCost,

    bandwidthLabel,

    bandwidthRatePerMbps,

    nrcRows,

    arcRows,

    totalNRC,

    totalARC,

    grandTotal,

    pricingSnapshot:
      clonePricing(config)
  };
}


/* ============================================
   OPTIONAL GLOBAL ACCESS
   ============================================ */

window.DEFAULT_PRICING =
  DEFAULT_PRICING;

window.getPricingConfig =
  getPricingConfig;

window.savePricingConfig =
  savePricingConfig;

window.resetPricingConfig =
  resetPricingConfig;

window.bandwidthToMbps =
  bandwidthToMbps;

window.estimateBandwidthCost =
  estimateBandwidthCost;

window.estimateCustomBandwidthCost =
  estimateCustomBandwidthCost;

window.calculateEstimate =
  calculateEstimate;
