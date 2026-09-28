/* ============================================
   app.js — shared utilities & navigation
   ============================================ */

/** Format a number as Naira currency, e.g. 195000 -> ₦195,000.00 */
function formatNaira(amount) {
  const n = Number(amount) || 0;
  return '₦' + n.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** Format a number as Naira without decimals for table rates */
function formatNairaWhole(amount) {
  const n = Number(amount) || 0;
  return '₦' + n.toLocaleString('en-NG', { maximumFractionDigits: 0 });
}

/** Generate a prototype reference number, e.g. GBB-2026-000123 */
function generateReference() {
  const year = new Date().getFullYear();
  const rand = Math.floor(100000 + Math.random() * 900000).toString().slice(0, 6);
  return `GBB-${year}-${rand}`;
}

/** Mobile navigation drawer wiring — call on every page after DOM load */
function initMobileNav() 
{
  const hamburger = document.querySelector('.hamburger-btn');
  const drawer = document.querySelector('.sidebar.mobile-drawer');
  const overlay = document.querySelector('.nav-overlay');
  if (!hamburger || !drawer || !overlay) return;

  function open() {
    drawer.classList.add('open');
    overlay.classList.add('open');
    hamburger.setAttribute('aria-expanded', 'true');
  }
  function close() {
    drawer.classList.remove('open');
    overlay.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
  }
  hamburger.addEventListener('click', open);
  overlay.addEventListener('click', close);
  drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', close));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') close();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
});
