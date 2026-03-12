/**
 * conduit-script.js — Listening Post frontend logic
 * Handles the Conduit assessment UI interactions
 */
(function() {
  'use strict';

  const API = '';

  async function fetchJSON(url, opts) {
    const resp = await fetch(url, opts);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
  }

  // Load pillar reference data on page load
  async function loadPillars() {
    try {
      const data = await fetchJSON(API + '/conduit/pillars');
      const container = document.getElementById('pillarReference');
      if (!container || !data.pillars) return;
      container.innerHTML = data.pillars.map(p => `
        <div class="ref-card">
          <div class="ref-header">${p.number} — ${p.title}</div>
          <p class="ref-doctrine">${p.doctrine}</p>
        </div>
      `).join('');
    } catch (e) {
      console.log('Could not load pillars:', e);
    }
  }

  document.addEventListener('DOMContentLoaded', loadPillars);
})();
