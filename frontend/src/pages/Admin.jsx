// import { useState } from 'react'

// import {
//   DEFAULT_PRICING,
//   getPricingConfig,
//   savePricingConfig,
// } from '../services/pricing'


// // Creates the default structure for a new custom BOQ item.
// const createEmptyItem = () => ({
//   id: `custom-${Date.now()}`,
//   description: '',
//   rate: 0,
//   type: 'One-Off',
//   unit: 'each',
//   quantityType: 'fixed',
//   enabled: true,
// })


// export default function Admin() {

//   /*
//     Load the current pricing configuration when the Admin page opens.

//     getPricingConfig() checks localStorage.

//     If the administrator has previously saved prices,
//     those prices will be loaded.

//     Otherwise, the default pricing configuration is returned.
//   */
//   const [config, setConfig] = useState(() => getPricingConfig())


//   // Used to show "Changes saved" after clicking Save.
//   const [saved, setSaved] = useState(false)


//   /*
//     Update one of the four built-in pricing items.

//     Example:

//     updateCoreItem('fibre', 'rate', 5000)

//     means:

//     items
//       └── fibre
//             └── rate = 5000
//   */
//   const updateCoreItem = (key, field, value) => {

//     setConfig(current => ({
//       ...current,

//       items: {
//         ...current.items,

//         [key]: {
//           ...current.items[key],

//           /*
//             Rate values must be numbers.

//             Text fields such as description and unit
//             remain strings.
//           */
//           [field]:
//             field === 'rate' || field === 'ratePerMbps'
//               ? Number(value) || 0
//               : value,
//         },
//       },
//     }))

//     // The current configuration has changed,
//     // so the "saved" message should disappear.
//     setSaved(false)
//   }


//   /*
//     Update one of the administrator-created BOQ items.
//   */
//   const updateCustomItem = (id, field, value) => {

//     setConfig(current => ({
//       ...current,

//       additionalItems: (current.additionalItems || []).map(item => {

//         // Find the item we want to change.
//         if (item.id !== id) {
//           return item
//         }

//         // Return the updated version of that item.
//         return {
//           ...item,

//           [field]:
//             field === 'rate'
//               ? Number(value) || 0
//               : value,
//         }
//       }),
//     }))

//     setSaved(false)
//   }


//   /*
//     Add a new empty BOQ item.
//   */
//   const addItem = () => {

//     setConfig(current => ({
//       ...current,

//       additionalItems: [
//         ...(current.additionalItems || []),
//         createEmptyItem(),
//       ],
//     }))

//     setSaved(false)
//   }


//   /*
//     Remove an additional BOQ item.

//     filter() creates a new array without the item
//     whose ID matches the ID we want to remove.
//   */
//   const removeItem = id => {

//     setConfig(current => ({
//       ...current,

//       additionalItems: (current.additionalItems || []).filter(
//         item => item.id !== id
//       ),
//     }))

//     setSaved(false)
//   }


//   /*
//     Save the current configuration.

//     This eventually calls localStorage through
//     savePricingConfig().
//   */
//   const handleSave = () => {

//     savePricingConfig(config)

//     setSaved(true)
//   }


//   /*
//     Restore the original default prices.

//     structuredClone() creates a separate copy so that
//     we don't accidentally modify DEFAULT_PRICING itself.
//   */
//   const handleReset = () => {

//     const fresh = structuredClone(DEFAULT_PRICING)

//     savePricingConfig(fresh)

//     setConfig(fresh)

//     setSaved(true)
//   }


//   /*
//     These are the four built-in pricing items.

//     The first value is the key used inside config.items.

//     The second value is the human-readable name displayed
//     to the administrator.
//   */
//   const coreItems = [
//     ['fibre', 'Fibre last mile'],
//     ['rack', '12U Rack'],
//     ['router', 'Router lease'],
//     ['bandwidth', 'Internet bandwidth'],
//   ]


//   return (
//     <div className="admin-page">

//       {/* =========================
//           ADMIN HEADER
//           ========================= */}
//       <header className="admin-header">

//         <div>

//           <p className="admin-eyebrow">
//             GBB Fibre Estimator
//           </p>

//           <h1>
//             Admin Dashboard
//           </h1>

//           <p className="muted">
//             Manage the pricing rules used by customer estimates.
//           </p>

//         </div>


//         {/* Return to the customer estimator */}
//         <a
//           className="btn btn-secondary"
//           href="/"
//         >
//           ← Back to Estimator
//         </a>

//       </header>



//       {/* =========================
//           CORE PRICING
//           ========================= */}
//       <section className="card admin-section">

//         <div className="admin-section-header">

//           <div>

//             <h2>
//               Core Pricing
//             </h2>

//             <p className="muted">
//               These four items are used directly by the estimator.
//             </p>

//           </div>

//         </div>


//         <div className="admin-table-wrap">

//           <table className="admin-table">

//             <thead>

//               <tr>

//                 <th>
//                   Item
//                 </th>

//                 <th>
//                   Description
//                 </th>

//                 <th>
//                   Rate
//                 </th>

//                 <th>
//                   Charge Type
//                 </th>

//                 <th>
//                   Unit
//                 </th>

//               </tr>

//             </thead>


//             <tbody>

//               {coreItems.map(([key, label]) => {

//                 const item = config.items[key]


//                 /*
//                   Fibre, rack and router use:

//                   item.rate

//                   Bandwidth uses:

//                   item.ratePerMbps
//                 */
//                 const rateField =
//                   key === 'bandwidth'
//                     ? 'ratePerMbps'
//                     : 'rate'


//                 return (

//                   <tr key={key}>

//                     <td>
//                       <strong>
//                         {label}
//                       </strong>
//                     </td>


//                     {/* Description */}
//                     <td>

//                       <input
//                         value={item.description || ''}
//                         onChange={event =>
//                           updateCoreItem(
//                             key,
//                             'description',
//                             event.target.value
//                           )
//                         }
//                       />

//                     </td>


//                     {/* Rate */}
//                     <td>

//                       <input
//                         type="number"
//                         min="0"
//                         value={item[rateField] ?? 0}
//                         onChange={event =>
//                           updateCoreItem(
//                             key,
//                             rateField,
//                             event.target.value
//                           )
//                         }
//                       />

//                       {key === 'bandwidth' && (
//                         <small>
//                           per Mbps
//                         </small>
//                       )}

//                     </td>


//                     {/* One-Off / Recurring */}
//                     <td>

//                       <select
//                         value={item.type || 'Recurring'}
//                         onChange={event =>
//                           updateCoreItem(
//                             key,
//                             'type',
//                             event.target.value
//                           )
//                         }
//                       >

//                         <option>
//                           One-Off
//                         </option>

//                         <option>
//                           Recurring
//                         </option>

//                       </select>

//                     </td>


//                     {/* Unit */}
//                     <td>

//                       <input
//                         value={item.unit || 'each'}
//                         onChange={event =>
//                           updateCoreItem(
//                             key,
//                             'unit',
//                             event.target.value
//                           )
//                         }
//                       />

//                     </td>

//                   </tr>

//                 )

//               })}

//             </tbody>

//           </table>

//         </div>

//       </section>



//       {/* =========================
//           ADDITIONAL BOQ ITEMS
//           ========================= */}
//       <section className="card admin-section">

//         <div className="admin-section-header">

//           <div>

//             <h2>
//               Additional BOQ Items
//             </h2>

//             <p className="muted">
//               Add optional items that should be included
//               automatically in future estimates.
//             </p>

//           </div>


//           <button
//             className="btn btn-secondary"
//             onClick={addItem}
//           >
//             + Add Item
//           </button>

//         </div>


//         {(config.additionalItems || []).length === 0 ? (

//           <div className="admin-empty">

//             No additional BOQ items configured.

//           </div>

//         ) : (

//           <div className="admin-items">

//             {config.additionalItems.map(item => (

//               <div
//                 className="admin-item"
//                 key={item.id}
//               >

//                 <div className="admin-item-grid">


//                   {/* Description */}
//                   <label>

//                     Description

//                     <input
//                       value={item.description}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'description',
//                           event.target.value
//                         )
//                       }
//                     />

//                   </label>



//                   {/* Rate */}
//                   <label>

//                     Rate

//                     <input
//                       type="number"
//                       min="0"
//                       value={item.rate}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'rate',
//                           event.target.value
//                         )
//                       }
//                     />

//                   </label>



//                   {/* Charge type */}
//                   <label>

//                     Charge Type

//                     <select
//                       value={item.type}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'type',
//                           event.target.value
//                         )
//                       }
//                     >

//                       <option>
//                         One-Off
//                       </option>

//                       <option>
//                         Recurring
//                       </option>

//                     </select>

//                   </label>



//                   {/* Unit */}
//                   <label>

//                     Unit

//                     <input
//                       value={item.unit}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'unit',
//                           event.target.value
//                         )
//                       }
//                     />

//                   </label>



//                   {/* Quantity basis */}
//                   <label>

//                     Quantity Basis

//                     <select
//                       value={item.quantityType}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'quantityType',
//                           event.target.value
//                         )
//                       }
//                     >

//                       <option value="fixed">
//                         Fixed (1)
//                       </option>

//                       <option value="distance">
//                         Fibre distance (m)
//                       </option>

//                     </select>

//                   </label>



//                   {/* Enable / disable */}
//                   <label className="checkbox-field">

//                     <span>
//                       Enabled
//                     </span>

//                     <input
//                       type="checkbox"
//                       checked={item.enabled !== false}
//                       onChange={event =>
//                         updateCustomItem(
//                           item.id,
//                           'enabled',
//                           event.target.checked
//                         )
//                       }
//                     />

//                   </label>

//                 </div>


//                 {/* Remove item */}
//                 <button
//                   className="btn btn-danger"
//                   onClick={() => removeItem(item.id)}
//                 >
//                   Remove
//                 </button>

//               </div>

//             ))}

//           </div>

//         )}

//       </section>



//       {/* =========================
//           NETWORK DATA
//           ========================= */}
//       <section className="card admin-section network-placeholder">

//         <div>

//           <h2>
//             Network Data
//           </h2>

//           <p className="muted">
//             KMZ/network topology management will plug into
//             this section. The current estimator still uses
//             the prototype POP data.
//           </p>

//         </div>


//         <span className="status-pill">
//           Prototype
//         </span>

//       </section>



//       {/* =========================
//           SAVE / RESET
//           ========================= */}
//       <div className="admin-actions">

//         <button
//           className="btn btn-secondary"
//           onClick={handleReset}
//         >
//           Reset Defaults
//         </button>


//         <button
//           className="btn btn-primary"
//           onClick={handleSave}
//         >
//           Save Pricing
//         </button>


//         {saved && (
//           <span className="save-message">
//             Changes saved.
//           </span>
//         )}

//       </div>

//     </div>
//   )
// }


// Admin.jsx
// -----------------------------------------------------------------------------
// Admin dashboard (/gbb/admin).
//
// Pricing is stored in the backend as "BOQ items":
//   GET    /admin/boq-items/        load everything
//   POST   /admin/boq-items/        add a custom item
//   PATCH  /admin/boq-items/{id}    edit an item
//   DELETE /admin/boq-items/{id}    remove a custom item
//
// Every admin call needs a JWT, so this page shows a login form first
// (POST /auth/login).
// -----------------------------------------------------------------------------

import { useEffect, useRef, useState } from 'react'

import { clearToken, getToken } from '../services/api'
import {
  createBoqItem,
  deleteBoqItem,
  listBoqItems,
  loginAdmin,
  updateBoqItem,
} from '../services/admin'

const errorBoxStyle = {
  marginBottom: 16,
  padding: '10px 12px',
  borderRadius: 8,
  background: '#FEF3F2',
  color: '#B42318',
  fontSize: 13.5,
}

// The four built-in items and the label shown for each.
const coreItems = [
  ['fibre', 'Fibre last mile'],
  ['rack', '12U Rack'],
  ['router', 'Router lease'],
  ['bandwidth', 'Internet bandwidth'],
]

// Fields the admin can edit in the UI. Used to detect what changed.
const EDITABLE = ['description', 'rate', 'unit', 'type', 'quantityType', 'enabled']


// -----------------------------------------------------------------------------
// Backend ⇄ UI mapping
// -----------------------------------------------------------------------------
//
//   UI field        backend field
//   description  ↔  name (also sent as description)
//   rate         ↔  rate        (bandwidth: price per Mbps)
//   unit         ↔  unit
//   type         ↔  chargeType  ('One-Off' ↔ 'one_off', 'Recurring' ↔ 'recurring')
//   quantityType ↔  computationMode ('fixed' ↔ 'flat', 'distance' ↔ 'quantity')
//   enabled      ↔  isActive
//
function fromServer(item) {
  return {
    id: item.id,
    tempId: null,
    key: item.key,
    isCustom: item.isCustom,
    description: item.name,
    rate: item.rate,
    unit: item.unit,
    type: item.chargeType === 'recurring' ? 'Recurring' : 'One-Off',
    quantityType: item.computationMode === 'flat' ? 'fixed' : 'distance',
    enabled: item.isActive,
  }
}

function toServer(item) {
  const payload = {
    name: item.description,
    description: item.description,
    rate: Number(item.rate) || 0,
    unit: item.unit || 'each',
    chargeType: item.type === 'Recurring' ? 'recurring' : 'one_off',
  }

  // Built-in items keep their computation mode and active flag untouched.
  if (item.isCustom) {
    payload.computationMode =
      item.quantityType === 'distance' ? 'quantity' : 'flat'
    payload.isActive = item.enabled !== false
  }

  return payload
}

const createEmptyItem = () => ({
  id: null,
  tempId: `new-${Date.now()}`,
  key: null,
  isCustom: true,
  description: '',
  rate: 0,
  type: 'One-Off',
  unit: 'each',
  quantityType: 'fixed',
  enabled: true,
})

const uidOf = item => item.id ?? item.tempId


// -----------------------------------------------------------------------------
// LOGIN
// -----------------------------------------------------------------------------

function AdminLogin({ onLoggedIn }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async event => {
    event.preventDefault()

    setSubmitting(true)
    setError('')

    try {
      await loginAdmin(email.trim(), password)
      onLoggedIn()
    } catch (err) {
      setError(err.message || 'Could not sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div>
          <p className="admin-eyebrow">GBB Fibre Estimator</p>
          <h1>Admin Sign In</h1>
        </div>

        <a className="btn btn-secondary" href="/">
          ← Back to Estimator
        </a>
      </header>

      <section className="card admin-section" style={{ maxWidth: 420 }}>
        <form onSubmit={handleSubmit}>
          {error && <div style={errorBoxStyle}>{error}</div>}

          <div className="field">
            <label htmlFor="admin-email">Email</label>
            <input
              id="admin-email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="admin-password">Password</label>
            <input
              id="admin-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="step-actions">
            <div style={{ flex: 1 }} />

            <button
              className="btn btn-primary"
              type="submit"
              disabled={submitting}
            >
              {submitting ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}


// -----------------------------------------------------------------------------
// DASHBOARD
// -----------------------------------------------------------------------------

function AdminDashboard({ onLogout }) {
  // Working copy the admin edits.
  const [items, setItems] = useState([])

  // IDs of saved custom items the admin removed (deleted on Save).
  const [deletedIds, setDeletedIds] = useState([])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  // Snapshot of what the server last returned, used to find changed items.
  const originalRef = useRef(new Map())

  // An expired/invalid token sends the admin back to the login form.
  const handleError = err => {
    if (err.status === 401 || err.status === 403) {
      onLogout()
      return
    }
    setError(err.message || 'Something went wrong.')
  }

  // Load all BOQ items from the backend.
  const load = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await listBoqItems()
      const mapped = data.map(fromServer)

      originalRef.current = new Map(mapped.map(i => [i.id, { ...i }]))
      setItems(mapped)
      setDeletedIds([])
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Edit one field of one item (built-in or custom).
  const updateItem = (uid, field, value) => {
    setItems(current =>
      current.map(item => {
        if (uidOf(item) !== uid) return item

        return {
          ...item,
          [field]: field === 'rate' ? Number(value) || 0 : value,
        }
      }),
    )

    setSaved(false)
  }

  const addItem = () => {
    setItems(current => [...current, createEmptyItem()])
    setSaved(false)
  }

  const removeItem = uid => {
    const target = items.find(item => uidOf(item) === uid)

    // Items that exist on the server are deleted when the admin saves.
    if (target?.id != null) {
      setDeletedIds(current => [...current, target.id])
    }

    setItems(current => current.filter(item => uidOf(item) !== uid))
    setSaved(false)
  }

  // Send every change to the backend.
  const handleSave = async () => {
    const customItems = items.filter(i => i.isCustom)

    if (customItems.some(i => !i.description.trim())) {
      setError('Every additional item needs a description.')
      return
    }

    setSaving(true)
    setError('')
    setSaved(false)

    try {
      // 1. Deletions
      for (const id of deletedIds) {
        await deleteBoqItem(id)
      }

      // 2. New items and edits
      for (const item of items) {
        if (item.id == null) {
          const created = await createBoqItem({
            name: item.description,
            description: item.description,
            rate: Number(item.rate) || 0,
            unit: item.unit || 'each',
            chargeType: item.type === 'Recurring' ? 'recurring' : 'one_off',
            computationMode:
              item.quantityType === 'distance' ? 'quantity' : 'flat',
          })

          // The create endpoint always makes active items.
          if (item.enabled === false) {
            await updateBoqItem(created.id, { isActive: false })
          }
          continue
        }

        const original = originalRef.current.get(item.id)
        const changed =
          !original || EDITABLE.some(field => item[field] !== original[field])

        if (changed) {
          await updateBoqItem(item.id, toServer(item))
        }
      }

      // 3. Reload so the screen shows exactly what the server now holds.
      await load()
      setSaved(true)
    } catch (err) {
      handleError(err)
      // Some changes may have been applied: re-sync with the server.
      await load()
    } finally {
      setSaving(false)
    }
  }

  // Throw away unsaved edits by reloading from the server.
  const handleDiscard = async () => {
    await load()
    setSaved(false)
  }

  const customList = items.filter(item => item.isCustom)

  return (
    <div className="admin-page">

      {/* ADMIN HEADER */}
      <header className="admin-header">
        <div>
          <p className="admin-eyebrow">GBB Fibre Estimator</p>
          <h1>Admin Dashboard</h1>
          <p className="muted">
            Manage the pricing rules used by customer estimates.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <a className="btn btn-secondary" href="/">
            ← Back to Estimator
          </a>

          <button className="btn btn-secondary" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      {error && <div style={errorBoxStyle}>{error}</div>}

      {loading ? (
        <section className="card admin-section">
          <p className="muted">Loading pricing...</p>
        </section>
      ) : (
        <>
          {/* CORE PRICING */}
          <section className="card admin-section">
            <div className="admin-section-header">
              <div>
                <h2>Core Pricing</h2>
                <p className="muted">
                  These four items are used directly by the estimator.
                </p>
              </div>
            </div>

            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Item</th>
                    <th>Description</th>
                    <th>Rate</th>
                    <th>Charge Type</th>
                    <th>Unit</th>
                  </tr>
                </thead>

                <tbody>
                  {coreItems.map(([key, label]) => {
                    const item = items.find(i => i.key === key)

                    // The four built-ins are created by `python seed.py`.
                    if (!item) {
                      return (
                        <tr key={key}>
                          <td>
                            <strong>{label}</strong>
                          </td>
                          <td colSpan="4" className="muted">
                            Not found on the server. Run seed.py on the
                            backend.
                          </td>
                        </tr>
                      )
                    }

                    const uid = uidOf(item)

                    return (
                      <tr key={key}>
                        <td>
                          <strong>{label}</strong>
                        </td>

                        <td>
                          <input
                            value={item.description || ''}
                            onChange={e =>
                              updateItem(uid, 'description', e.target.value)
                            }
                          />
                        </td>

                        <td>
                          <input
                            type="number"
                            min="0"
                            value={item.rate ?? 0}
                            onChange={e =>
                              updateItem(uid, 'rate', e.target.value)
                            }
                          />

                          {key === 'bandwidth' && <small>per Mbps</small>}
                        </td>

                        <td>
                          <select
                            value={item.type}
                            onChange={e =>
                              updateItem(uid, 'type', e.target.value)
                            }
                          >
                            <option>One-Off</option>
                            <option>Recurring</option>
                          </select>
                        </td>

                        <td>
                          <input
                            value={item.unit || ''}
                            onChange={e =>
                              updateItem(uid, 'unit', e.target.value)
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

          {/* ADDITIONAL BOQ ITEMS */}
          <section className="card admin-section">
            <div className="admin-section-header">
              <div>
                <h2>Additional BOQ Items</h2>
                <p className="muted">
                  Add optional items that should be included automatically in
                  future estimates.
                </p>
              </div>

              <button className="btn btn-secondary" onClick={addItem}>
                + Add Item
              </button>
            </div>

            {customList.length === 0 ? (
              <div className="admin-empty">
                No additional BOQ items configured.
              </div>
            ) : (
              <div className="admin-items">
                {customList.map(item => {
                  const uid = uidOf(item)

                  return (
                    <div className="admin-item" key={uid}>
                      <div className="admin-item-grid">

                        <label>
                          Description
                          <input
                            value={item.description}
                            onChange={e =>
                              updateItem(uid, 'description', e.target.value)
                            }
                          />
                        </label>

                        <label>
                          Rate
                          <input
                            type="number"
                            min="0"
                            value={item.rate}
                            onChange={e =>
                              updateItem(uid, 'rate', e.target.value)
                            }
                          />
                        </label>

                        <label>
                          Charge Type
                          <select
                            value={item.type}
                            onChange={e =>
                              updateItem(uid, 'type', e.target.value)
                            }
                          >
                            <option>One-Off</option>
                            <option>Recurring</option>
                          </select>
                        </label>

                        <label>
                          Unit
                          <input
                            value={item.unit}
                            onChange={e =>
                              updateItem(uid, 'unit', e.target.value)
                            }
                          />
                        </label>

                        <label>
                          Quantity Basis
                          <select
                            value={item.quantityType}
                            onChange={e =>
                              updateItem(uid, 'quantityType', e.target.value)
                            }
                          >
                            <option value="fixed">Fixed (1)</option>

                            {/* The backend currently always uses quantity 1
                                for custom items, so this option is disabled
                                until the backend supports it. */}
                            <option value="distance" disabled>
                              Fibre distance (m) — not supported yet
                            </option>
                          </select>
                        </label>

                        <label className="checkbox-field">
                          <span>Enabled</span>
                          <input
                            type="checkbox"
                            checked={item.enabled !== false}
                            onChange={e =>
                              updateItem(uid, 'enabled', e.target.checked)
                            }
                          />
                        </label>

                      </div>

                      <button
                        className="btn btn-danger"
                        onClick={() => removeItem(uid)}
                      >
                        Remove
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </section>

          {/* NETWORK DATA (placeholder, unchanged) */}
          <section className="card admin-section network-placeholder">
            <div>
              <h2>Network Data</h2>

              <p className="muted">
                KMZ/network topology management will plug into this section.
              </p>
            </div>

            <span className="status-pill">Coming soon</span>
          </section>

          {/* SAVE / DISCARD */}
          <div className="admin-actions">
            <button
              className="btn btn-secondary"
              onClick={handleDiscard}
              disabled={saving}
            >
              Discard Changes
            </button>

            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Pricing'}
            </button>

            {saved && (
              <span className="save-message">Changes saved.</span>
            )}
          </div>
        </>
      )}
    </div>
  )
}


// -----------------------------------------------------------------------------
// PAGE
// -----------------------------------------------------------------------------

export default function Admin() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()))

  const logout = () => {
    clearToken()
    setAuthed(false)
  }

  if (!authed) {
    return <AdminLogin onLoggedIn={() => setAuthed(true)} />
  }

  return <AdminDashboard onLogout={logout} />
}
