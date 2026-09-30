import { useState } from 'react'

import {
  DEFAULT_PRICING,
  getPricingConfig,
  savePricingConfig,
} from '../services/pricing'


// Creates the default structure for a new custom BOQ item.
const createEmptyItem = () => ({
  id: `custom-${Date.now()}`,
  description: '',
  rate: 0,
  type: 'One-Off',
  unit: 'each',
  quantityType: 'fixed',
  enabled: true,
})


export default function Admin() {

  /*
    Load the current pricing configuration when the Admin page opens.

    getPricingConfig() checks localStorage.

    If the administrator has previously saved prices,
    those prices will be loaded.

    Otherwise, the default pricing configuration is returned.
  */
  const [config, setConfig] = useState(() => getPricingConfig())


  // Used to show "Changes saved" after clicking Save.
  const [saved, setSaved] = useState(false)


  /*
    Update one of the four built-in pricing items.

    Example:

    updateCoreItem('fibre', 'rate', 5000)

    means:

    items
      └── fibre
            └── rate = 5000
  */
  const updateCoreItem = (key, field, value) => {

    setConfig(current => ({
      ...current,

      items: {
        ...current.items,

        [key]: {
          ...current.items[key],

          /*
            Rate values must be numbers.

            Text fields such as description and unit
            remain strings.
          */
          [field]:
            field === 'rate' || field === 'ratePerMbps'
              ? Number(value) || 0
              : value,
        },
      },
    }))

    // The current configuration has changed,
    // so the "saved" message should disappear.
    setSaved(false)
  }


  /*
    Update one of the administrator-created BOQ items.
  */
  const updateCustomItem = (id, field, value) => {

    setConfig(current => ({
      ...current,

      additionalItems: (current.additionalItems || []).map(item => {

        // Find the item we want to change.
        if (item.id !== id) {
          return item
        }

        // Return the updated version of that item.
        return {
          ...item,

          [field]:
            field === 'rate'
              ? Number(value) || 0
              : value,
        }
      }),
    }))

    setSaved(false)
  }


  /*
    Add a new empty BOQ item.
  */
  const addItem = () => {

    setConfig(current => ({
      ...current,

      additionalItems: [
        ...(current.additionalItems || []),
        createEmptyItem(),
      ],
    }))

    setSaved(false)
  }


  /*
    Remove an additional BOQ item.

    filter() creates a new array without the item
    whose ID matches the ID we want to remove.
  */
  const removeItem = id => {

    setConfig(current => ({
      ...current,

      additionalItems: (current.additionalItems || []).filter(
        item => item.id !== id
      ),
    }))

    setSaved(false)
  }


  /*
    Save the current configuration.

    This eventually calls localStorage through
    savePricingConfig().
  */
  const handleSave = () => {

    savePricingConfig(config)

    setSaved(true)
  }


  /*
    Restore the original default prices.

    structuredClone() creates a separate copy so that
    we don't accidentally modify DEFAULT_PRICING itself.
  */
  const handleReset = () => {

    const fresh = structuredClone(DEFAULT_PRICING)

    savePricingConfig(fresh)

    setConfig(fresh)

    setSaved(true)
  }


  /*
    These are the four built-in pricing items.

    The first value is the key used inside config.items.

    The second value is the human-readable name displayed
    to the administrator.
  */
  const coreItems = [
    ['fibre', 'Fibre last mile'],
    ['rack', '12U Rack'],
    ['router', 'Router lease'],
    ['bandwidth', 'Internet bandwidth'],
  ]


  return (
    <div className="admin-page">

      {/* =========================
          ADMIN HEADER
          ========================= */}
      <header className="admin-header">

        <div>

          <p className="admin-eyebrow">
            GBB Fibre Estimator
          </p>

          <h1>
            Admin Dashboard
          </h1>

          <p className="muted">
            Manage the pricing rules used by customer estimates.
          </p>

        </div>


        {/* Return to the customer estimator */}
        <a
          className="btn btn-secondary"
          href="/"
        >
          ← Back to Estimator
        </a>

      </header>



      {/* =========================
          CORE PRICING
          ========================= */}
      <section className="card admin-section">

        <div className="admin-section-header">

          <div>

            <h2>
              Core Pricing
            </h2>

            <p className="muted">
              These four items are used directly by the estimator.
            </p>

          </div>

        </div>


        <div className="admin-table-wrap">

          <table className="admin-table">

            <thead>

              <tr>

                <th>
                  Item
                </th>

                <th>
                  Description
                </th>

                <th>
                  Rate
                </th>

                <th>
                  Charge Type
                </th>

                <th>
                  Unit
                </th>

              </tr>

            </thead>


            <tbody>

              {coreItems.map(([key, label]) => {

                const item = config.items[key]


                /*
                  Fibre, rack and router use:

                  item.rate

                  Bandwidth uses:

                  item.ratePerMbps
                */
                const rateField =
                  key === 'bandwidth'
                    ? 'ratePerMbps'
                    : 'rate'


                return (

                  <tr key={key}>

                    <td>
                      <strong>
                        {label}
                      </strong>
                    </td>


                    {/* Description */}
                    <td>

                      <input
                        value={item.description || ''}
                        onChange={event =>
                          updateCoreItem(
                            key,
                            'description',
                            event.target.value
                          )
                        }
                      />

                    </td>


                    {/* Rate */}
                    <td>

                      <input
                        type="number"
                        min="0"
                        value={item[rateField] ?? 0}
                        onChange={event =>
                          updateCoreItem(
                            key,
                            rateField,
                            event.target.value
                          )
                        }
                      />

                      {key === 'bandwidth' && (
                        <small>
                          per Mbps
                        </small>
                      )}

                    </td>


                    {/* One-Off / Recurring */}
                    <td>

                      <select
                        value={item.type || 'Recurring'}
                        onChange={event =>
                          updateCoreItem(
                            key,
                            'type',
                            event.target.value
                          )
                        }
                      >

                        <option>
                          One-Off
                        </option>

                        <option>
                          Recurring
                        </option>

                      </select>

                    </td>


                    {/* Unit */}
                    <td>

                      <input
                        value={item.unit || 'each'}
                        onChange={event =>
                          updateCoreItem(
                            key,
                            'unit',
                            event.target.value
                          )
                        }
                      />

                    </td>

                  </tr>

                )

              })}

            </tbody>

          </table>

        </div>

      </section>



      {/* =========================
          ADDITIONAL BOQ ITEMS
          ========================= */}
      <section className="card admin-section">

        <div className="admin-section-header">

          <div>

            <h2>
              Additional BOQ Items
            </h2>

            <p className="muted">
              Add optional items that should be included
              automatically in future estimates.
            </p>

          </div>


          <button
            className="btn btn-secondary"
            onClick={addItem}
          >
            + Add Item
          </button>

        </div>


        {(config.additionalItems || []).length === 0 ? (

          <div className="admin-empty">

            No additional BOQ items configured.

          </div>

        ) : (

          <div className="admin-items">

            {config.additionalItems.map(item => (

              <div
                className="admin-item"
                key={item.id}
              >

                <div className="admin-item-grid">


                  {/* Description */}
                  <label>

                    Description

                    <input
                      value={item.description}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'description',
                          event.target.value
                        )
                      }
                    />

                  </label>



                  {/* Rate */}
                  <label>

                    Rate

                    <input
                      type="number"
                      min="0"
                      value={item.rate}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'rate',
                          event.target.value
                        )
                      }
                    />

                  </label>



                  {/* Charge type */}
                  <label>

                    Charge Type

                    <select
                      value={item.type}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'type',
                          event.target.value
                        )
                      }
                    >

                      <option>
                        One-Off
                      </option>

                      <option>
                        Recurring
                      </option>

                    </select>

                  </label>



                  {/* Unit */}
                  <label>

                    Unit

                    <input
                      value={item.unit}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'unit',
                          event.target.value
                        )
                      }
                    />

                  </label>



                  {/* Quantity basis */}
                  <label>

                    Quantity Basis

                    <select
                      value={item.quantityType}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'quantityType',
                          event.target.value
                        )
                      }
                    >

                      <option value="fixed">
                        Fixed (1)
                      </option>

                      <option value="distance">
                        Fibre distance (m)
                      </option>

                    </select>

                  </label>



                  {/* Enable / disable */}
                  <label className="checkbox-field">

                    <span>
                      Enabled
                    </span>

                    <input
                      type="checkbox"
                      checked={item.enabled !== false}
                      onChange={event =>
                        updateCustomItem(
                          item.id,
                          'enabled',
                          event.target.checked
                        )
                      }
                    />

                  </label>

                </div>


                {/* Remove item */}
                <button
                  className="btn btn-danger"
                  onClick={() => removeItem(item.id)}
                >
                  Remove
                </button>

              </div>

            ))}

          </div>

        )}

      </section>



      {/* =========================
          NETWORK DATA
          ========================= */}
      <section className="card admin-section network-placeholder">

        <div>

          <h2>
            Network Data
          </h2>

          <p className="muted">
            KMZ/network topology management will plug into
            this section. The current estimator still uses
            the prototype POP data.
          </p>

        </div>


        <span className="status-pill">
          Prototype
        </span>

      </section>



      {/* =========================
          SAVE / RESET
          ========================= */}
      <div className="admin-actions">

        <button
          className="btn btn-secondary"
          onClick={handleReset}
        >
          Reset Defaults
        </button>


        <button
          className="btn btn-primary"
          onClick={handleSave}
        >
          Save Pricing
        </button>


        {saved && (
          <span className="save-message">
            Changes saved.
          </span>
        )}

      </div>

    </div>
  )
}