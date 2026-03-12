/**
 * Praxis Journey — AI Decision Engine frontend
 * Uses the /stack endpoint for composed stack recommendations
 * and /profile for persisting user profiles.
 */

let currentStep = 1;
let journey = { task: null, industry: null, budget: null, skill: null };
let lastStackResult = null;   // stores the full /stack response

// ─────────────────────────────────────────────────────
// Option selection
// ─────────────────────────────────────────────────────
document.querySelectorAll('.option').forEach(opt => {
  opt.addEventListener('click', function () {
    const step = this.closest('.step');
    const stepNum = step.getAttribute('data-step');
    const value = this.getAttribute('data-value');

    step.querySelectorAll('.option').forEach(o => o.classList.remove('selected'));
    this.classList.add('selected');

    if (stepNum === '1') journey.task = value;
    else if (stepNum === '2') journey.industry = value;
    else if (stepNum === '3') journey.budget = value;
    else if (stepNum === '4') journey.skill = value;
  });
});

// ─────────────────────────────────────────────────────
// Navigation
// ─────────────────────────────────────────────────────
function nextStep() {
  const el = document.querySelector(`.step[data-step="${currentStep}"]`);
  if (!el.querySelector('.option.selected')) {
    alert('Please select an option to continue');
    return;
  }
  currentStep++;
  updateUI();
}

function prevStep() {
  if (currentStep > 1) { currentStep--; updateUI(); }
}

function updateUI() {
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  const target = document.querySelector(`.step[data-step="${currentStep}"]`);
  if (target) target.classList.add('active');
  document.getElementById('progress').style.width = (currentStep / 4) * 100 + '%';
}

// ─────────────────────────────────────────────────────
// Finish — call /profile then /stack
// ─────────────────────────────────────────────────────
async function finishJourney() {
  const el = document.querySelector(`.step[data-step="${currentStep}"]`);
  if (!el.querySelector('.option.selected')) {
    alert('Please select an option to continue');
    return;
  }

  // Show loading state
  const btn = el.querySelector('.btn-primary');
  const origText = btn ? btn.textContent : '';
  if (btn) { btn.textContent = 'Building your stack…'; btn.disabled = true; }

  // 1. Persist profile
  try {
    await fetch('/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        profile_id: 'journey',
        industry: journey.industry,
        budget: journey.budget,
        skill_level: journey.skill,
        goals: [journey.task],
      }),
    });
  } catch (e) { console.warn('Profile save skipped', e); }

  // 2. Get stack recommendation
  const query = `I need help with ${journey.task} in the ${journey.industry} industry`;
  try {
    const res = await fetch('/stack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, profile_id: 'journey', stack_size: 3 }),
    });
    if (!res.ok) throw new Error(`Stack endpoint returned ${res.status}`);
    lastStackResult = await res.json();
  } catch (e) {
    console.error('Stack fetch failed, falling back to /search', e);
    try {
      const res2 = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, profile_id: 'journey' }),
      });
      if (!res2.ok) throw new Error(`Search endpoint returned ${res2.status}`);
      const tools = await res2.json();
      lastStackResult = { stack: tools.map((t, i) => ({ ...t, role: i === 0 ? 'primary' : 'companion' })), narrative: null };
    } catch (e2) {
      console.error('Both /stack and /search failed', e2);
      lastStackResult = { stack: [], narrative: 'Could not reach the server. Please make sure the Praxis API is running and try again.' };
    }
  }

  showResults(lastStackResult);
  currentStep = 5;
  updateUI();
}

// ─────────────────────────────────────────────────────
// Results renderer — stack-aware
// ─────────────────────────────────────────────────────
function showResults(data) {
  const resultsEl = document.getElementById('results-step');
  const savedStack = JSON.parse(localStorage.getItem('savedStack') || '[]');
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';

  const profileMap = {
    task: cap(journey.task), industry: cap(journey.industry),
    budget: cap(journey.budget), skill: cap(journey.skill),
  };

  let html = `
    <h2>Your AI Stack</h2>
    <p class="results-subtitle">Personalized for ${profileMap.task} · ${profileMap.industry} · ${profileMap.budget}</p>

    <div class="profile">
      <div class="profile-item"><div class="profile-label">Task</div><div class="profile-value">${profileMap.task}</div></div>
      <div class="profile-item"><div class="profile-label">Industry</div><div class="profile-value">${profileMap.industry}</div></div>
      <div class="profile-item"><div class="profile-label">Budget</div><div class="profile-value">${profileMap.budget}</div></div>
      <div class="profile-item"><div class="profile-label">Skill</div><div class="profile-value">${profileMap.skill}</div></div>
    </div>
  `;

  // Narrative
  if (data.narrative) {
    html += `<p class="stack-intro">${data.narrative}</p>`;
  } else {
    html += `<p class="stack-intro">Here's a stack tailored to your needs:</p>`;
  }

  // Stack fit + cost summary
  if (data.stack_fit_score || data.total_monthly_cost) {
    html += `<div style="display:flex;gap:1.5rem;margin-bottom:1.5rem;">`;
    if (data.stack_fit_score) html += `<div style="flex:1;background:rgba(255,255,255,0.035);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);box-shadow:0 2px 16px rgba(0,0,0,0.22),0 0 0 1px rgba(255,255,255,0.03);padding:1.5rem;border-radius:12px;text-align:center;"><div style="font-size:1.6rem;font-weight:bold;color:#6366f1;">${data.stack_fit_score}%</div><div style="font-size:0.8rem;color:rgba(255,255,255,0.50);margin-top:0.25rem;">Stack Fit</div></div>`;
    if (data.total_monthly_cost) html += `<div style="flex:1;background:rgba(255,255,255,0.035);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);box-shadow:0 2px 16px rgba(0,0,0,0.22),0 0 0 1px rgba(255,255,255,0.03);padding:1.5rem;border-radius:12px;text-align:center;"><div style="font-size:1.6rem;font-weight:bold;color:#6366f1;">${data.total_monthly_cost}</div><div style="font-size:0.8rem;color:rgba(255,255,255,0.50);margin-top:0.25rem;">Est. Monthly</div></div>`;
    html += `</div>`;
  }

  html += `<div class="stack-cards">`;

  const stack = data.stack || [];
  if (stack.length === 0) {
    html += '<p style="color:rgba(255,255,255,0.45);">No tools match your criteria. Try different options.</p>';
  } else {
    const roleLabel = { primary: '🏆 Primary', companion: '🤝 Companion', infrastructure: '🔗 Infrastructure', analytics: '📊 Analytics' };
    stack.forEach((entry) => {
      const name = entry.name;
      const role = entry.role || 'companion';
      const isSaved = savedStack.some(t => t.name === name);
      const fitScore = entry.fit_score || 0;
      const reasons = entry.reasons || entry.match_reasons || [];
      const caveats = entry.caveats || [];
      const pricing = entry.pricing || {};
      const skillLevel = entry.skill_level || '';

      html += `
        <div class="stack-card" style="${role === 'primary' ? 'box-shadow:inset 4px 0 0 #6366f1, 0 2px 16px rgba(0,0,0,0.22), 0 0 0 1px rgba(255,255,255,0.03);' : ''}">
          <div class="stack-card-header">
            <div class="stack-icon">${name.charAt(0).toUpperCase()}</div>
            <div class="stack-card-title" style="flex:1;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span>${name}</span>
                <span class="confidence-badge">${fitScore}% fit</span>
              </div>
              <div style="font-size:0.75rem;color:rgba(255,255,255,0.45);margin-top:2px;">${roleLabel[role] || role}</div>
            </div>
          </div>

          <div class="confidence-bar">
            <div class="confidence-fill" style="width:${fitScore}%;background:linear-gradient(90deg,#6366f1,#6366f1);"></div>
          </div>

          <div class="stack-card-desc">${entry.description || 'A powerful AI tool for your workflow.'}</div>
      `;

      // Reasons
      if (reasons.length > 0) {
        html += `<div class="stack-fit"><strong>Why this tool:</strong><ul style="margin:0.3rem 0 0 1rem;padding:0;">`;
        reasons.forEach(r => { html += `<li style="font-size:0.85rem;margin:0.15rem 0;">${r}</li>`; });
        html += `</ul></div>`;
      }

      // Caveats
      if (caveats.length > 0) {
        html += `<div style="background:rgba(240,173,78,0.08);padding:0.75rem 1rem;box-shadow:inset 3px 0 0 #f0ad4e;font-size:0.85rem;color:rgba(255,255,255,0.65);margin-top:0.75rem;border-radius:0 8px 8px 0;line-height:1.5;"><strong style="color:#f0ad4e;">Heads up:</strong> ${caveats.join(' · ')}</div>`;
      }

      // Pricing + skill badge row
      const priceParts = [];
      if (pricing.free_tier) priceParts.push('Free tier ✓');
      if (pricing.starter) priceParts.push('from $' + pricing.starter + '/mo');

      if (priceParts.length > 0 || skillLevel) {
        html += `<div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.5rem;">`;
        priceParts.forEach(p => { html += `<span class="tag" style="background:rgba(80,227,194,0.10);color:#50e3c2;padding:0.25rem 0.75rem;border-radius:8px;font-size:0.78rem;">${p}</span>`; });
        if (skillLevel) html += `<span class="tag" style="background:rgba(99,102,241,0.10);color:#818cf8;padding:0.25rem 0.75rem;border-radius:8px;font-size:0.78rem;">${cap(skillLevel)}</span>`;
        html += `</div>`;
      }

      // URL
      if (entry.url) {
        html += `<p style="margin-top:0.5rem;"><a href="${entry.url}" target="_blank" style="color:#50e3c2;text-decoration:none;font-weight:500;transition:color 0.18s;">Try ${name} →</a></p>`;
      }

      // Actions
      html += `
          <div class="stack-card-actions">
            <button class="action-btn-small ${isSaved ? 'saved' : ''}" onclick="toggleSaveStack('${name}',event)">${isSaved ? '⭐ Saved' : '☆ Save'}</button>
            <button class="action-btn-small" onclick="openCompare('${name}',event)">⚖️ Compare</button>
          </div>
          <div class="feedback-section">
            <span style="font-size:0.8rem;color:rgba(255,255,255,0.4);">Was this helpful?</span>
            <div style="display:flex;gap:0.5rem;">
              <button class="feedback-btn" onclick="recordFeedback('${name}','helpful',event)">👍</button>
              <button class="feedback-btn" onclick="recordFeedback('${name}','not_helpful',event)">👎</button>
            </div>
          </div>
        </div>
      `;
    });
  }

  html += `</div>`;

  // Integration notes
  if (data.integration_notes && data.integration_notes.length > 0) {
    html += `<div style="background:rgba(255,255,255,0.035);box-shadow:0 2px 16px rgba(0,0,0,0.22),0 0 0 1px rgba(255,255,255,0.03);padding:1.5rem;border-radius:12px;margin-top:1.5rem;"><strong style="color:rgba(255,255,255,0.85);">🔗 Integration Notes</strong><ul style="margin:0.5rem 0 0 1rem;padding:0;color:rgba(255,255,255,0.50);font-size:0.9rem;line-height:1.65;">`;
    data.integration_notes.forEach(n => { html += `<li style="margin:0.25rem 0;">${n}</li>`; });
    html += `</ul></div>`;
  }

  // Alternatives
  if (data.alternatives && data.alternatives.length > 0) {
    html += `<div style="margin-top:1.5rem;"><h3 style="font-size:1rem;margin-bottom:0.75rem;color:rgba(255,255,255,0.55);">Also Consider</h3><div style="display:flex;gap:0.5rem;flex-wrap:wrap;">`;
    data.alternatives.forEach(a => {
      const altUrl = a.url ? a.url : `/intelligence/${encodeURIComponent(a.name)}`;
      html += `<a href="${altUrl}" target="_blank" style="padding:0.5rem 1rem;background:rgba(255,255,255,0.04);box-shadow:0 1px 8px rgba(0,0,0,0.18),0 0 0 1px rgba(255,255,255,0.03);border-radius:8px;font-size:0.85rem;color:rgba(255,255,255,0.75);text-decoration:none;transition:all 0.2s;cursor:pointer;" onmouseover="this.style.background='rgba(99,102,241,0.10)';this.style.boxShadow='0 2px 12px rgba(99,102,241,0.12),0 0 0 1px rgba(99,102,241,0.25)';this.style.color='#f0f0f5';" onmouseout="this.style.background='rgba(255,255,255,0.04)';this.style.boxShadow='0 1px 8px rgba(0,0,0,0.18),0 0 0 1px rgba(255,255,255,0.03)';this.style.color='rgba(255,255,255,0.75)';">${a.name}</a>`;
    });
    html += `</div></div>`;
  }

  // Footer actions
  html += `
    <div class="action-buttons">
      <button class="action-btn-secondary" onclick="resetJourney()">← Start Over</button>
      <button class="action-btn-primary" onclick="window.location.href='/static/tools.html'">→ Explore All Tools</button>
    </div>
  `;

  resultsEl.innerHTML = html;
}

// ─────────────────────────────────────────────────────
// Reset
// ─────────────────────────────────────────────────────
function resetJourney() {
  currentStep = 1;
  journey = { task: null, industry: null, budget: null, skill: null };
  lastStackResult = null;
  document.querySelectorAll('.option.selected').forEach(o => o.classList.remove('selected'));
  updateUI();
}

// ─────────────────────────────────────────────────────
// Save to stack (localStorage)
// ─────────────────────────────────────────────────────
function toggleSaveStack(toolName, event) {
  event.preventDefault(); event.stopPropagation();
  const saved = JSON.parse(localStorage.getItem('savedStack') || '[]');
  const idx = saved.findIndex(t => t.name === toolName);
  if (idx >= 0) { saved.splice(idx, 1); }
  else { saved.push({ name: toolName, journey: { ...journey }, savedAt: new Date().toISOString() }); }
  localStorage.setItem('savedStack', JSON.stringify(saved));
  const btn = event.target.closest('button');
  btn.textContent = idx >= 0 ? '☆ Save' : '⭐ Saved';
  btn.classList.toggle('saved', idx < 0);
}

// ─────────────────────────────────────────────────────
// Compare — calls /compare endpoint
// ─────────────────────────────────────────────────────
function openCompare(toolName, event) {
  event.preventDefault(); event.stopPropagation();

  let modal = document.getElementById('comparison-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'comparison-modal';
    document.body.appendChild(modal);
  }

  // Build list of other tools from current stack
  const others = (lastStackResult?.stack || []).filter(e => e.name !== toolName);
  let listHtml = '';
  others.forEach(o => {
    listHtml += `<div class="comparison-option" onclick="runCompare('${toolName}','${o.name}')">${o.name}</div>`;
  });

  modal.innerHTML = `
    <div class="modal-overlay" onclick="closeComparison()"></div>
    <div class="modal-content">
      <button class="modal-close" onclick="closeComparison()">✕</button>
      <h3>Compare with…</h3>
      <p style="color:rgba(255,255,255,0.45);font-size:0.9rem;margin-bottom:1rem;">Select a tool to compare against <strong style="color:#f0f0f5;">${toolName}</strong></p>
      <div id="comparison-list">${listHtml || '<p style="color:rgba(255,255,255,0.4);">No other tools in this stack</p>'}</div>
      <div id="comparison-result"></div>
    </div>
  `;
  modal.style.display = 'flex';
}

async function runCompare(toolA, toolB) {
  const resultEl = document.getElementById('comparison-result');
  resultEl.innerHTML = '<p style="color:rgba(255,255,255,0.45);margin-top:1rem;">Loading comparison…</p>';

  try {
    const res = await fetch('/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_a: toolA, tool_b: toolB, profile_id: 'journey' }),
    });
    const cmp = await res.json();

    let html = `<div style="margin-top:1rem;padding:1.5rem;background:rgba(255,255,255,0.035);box-shadow:0 2px 16px rgba(0,0,0,0.22),0 0 0 1px rgba(255,255,255,0.03);border-radius:12px;">`;
    html += `<h4 style="margin-bottom:0.5rem;color:#f0f0f5;">${toolA} vs ${toolB}</h4>`;    

    // Side by side table
    const fields = [
      ['Skill Level', cmp.tool_a?.skill_level, cmp.tool_b?.skill_level],
      ['Categories', (cmp.tool_a?.categories || []).join(', '), (cmp.tool_b?.categories || []).join(', ')],
    ];
    html += `<table style="width:100%;font-size:0.85rem;border-collapse:collapse;color:rgba(255,255,255,0.75);line-height:1.5;">`;
    html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.04);"><th></th><th style="padding:0.5rem;color:#6366f1;">${toolA}</th><th style="padding:0.5rem;color:#50e3c2;">${toolB}</th></tr>`;
    fields.forEach(([label, a, b]) => {
      html += `<tr style="border-bottom:1px solid rgba(255,255,255,0.03);"><td style="padding:0.5rem;font-weight:500;color:rgba(255,255,255,0.50);">${label}</td><td style="padding:0.5rem;">${a || '—'}</td><td style="padding:0.5rem;">${b || '—'}</td></tr>`;
    });
    html += `</table>`;

    if (cmp.shared_integrations && cmp.shared_integrations.length > 0) {
      html += `<p style="margin-top:0.5rem;font-size:0.85rem;color:rgba(255,255,255,0.55);"><strong style="color:rgba(255,255,255,0.75);">Shared integrations:</strong> ${cmp.shared_integrations.join(', ')}</p>`;
    }
    if (cmp.recommendation) {
      html += `<p style="margin-top:0.75rem;padding:0.75rem 1rem;background:rgba(80,227,194,0.06);box-shadow:inset 2px 0 0 #50e3c2,0 1px 8px rgba(0,0,0,0.15);border-radius:0 8px 8px 0;font-size:0.9rem;color:rgba(255,255,255,0.75);line-height:1.5;"><strong style="color:#50e3c2;">Recommendation:</strong> ${cmp.recommendation}</p>`;
    }
    html += `</div>`;
    resultEl.innerHTML = html;
  } catch (e) {
    resultEl.innerHTML = `<p style="color:#ef4444;margin-top:1rem;">Comparison failed — ${e.message}</p>`;
  }
}

function closeComparison() {
  const m = document.getElementById('comparison-modal');
  if (m) m.style.display = 'none';
}

// ─────────────────────────────────────────────────────
// Feedback
// ─────────────────────────────────────────────────────
function recordFeedback(toolName, sentiment, event) {
  event.preventDefault(); event.stopPropagation();
  const accepted = sentiment === 'helpful';

  fetch('/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `I need help with ${journey.task}`,
      tool: toolName,
      accepted,
      rating: accepted ? 8 : 3,
      details: { journey, sentiment, feedback_type: 'journey_result' },
    }),
  }).catch(err => console.error('Feedback error:', err));

  const btn = event.target.closest('button');
  const original = btn.textContent;
  btn.textContent = '✓';
  btn.disabled = true;
  setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 2000);
}

// ─────────────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────────────
function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ''; }
updateUI();
