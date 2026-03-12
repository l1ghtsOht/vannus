async function search() {
  const q = document.getElementById('query').value;
  const filtersRaw = document.getElementById('filters').value;
  const filters = filtersRaw ? filtersRaw.split(',').map(s => s.trim()).filter(Boolean) : undefined;

  const body = { query: q };
  if (filters) body.filters = filters;

  const res = await fetch('/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  const payload = await res.json();
  const resultsEl = document.getElementById('results');
  const titleEl = document.getElementById('rec-title');
  resultsEl.innerHTML = '';

  // The /search endpoint returns { results: [...], meta: {...} }
  const data = payload.results || payload;
  const meta = payload.meta || {};

  if (!data || data.length === 0) {
    resultsEl.innerHTML = '<div class="empty">No matching tools found. Try different keywords.</div>';
    titleEl.style.display = 'none';
    return;
  }

  titleEl.style.display = 'block';

  // ── Query Reflection — "Here's what I understood" ──
  const reflectionEl = buildReflection(q, meta, data);
  if (reflectionEl) resultsEl.appendChild(reflectionEl);

  data.forEach((tool, idx) => {
    const card = document.createElement('div');
    card.className = 'card';

    // Header with icon and title
    const header = document.createElement('div');
    header.className = 'card-header';

    const icon = document.createElement('div');
    icon.className = 'card-icon';
    icon.textContent = tool.name.charAt(0).toUpperCase();
    header.appendChild(icon);

    const titleDiv = document.createElement('div');
    titleDiv.className = 'card-title';
    const h = document.createElement('h3');
    h.textContent = tool.name;
    titleDiv.appendChild(h);
    header.appendChild(titleDiv);

    card.appendChild(header);

    // Description
    const desc = document.createElement('p');
    desc.className = 'card-desc';
    desc.textContent = tool.description || 'A powerful AI tool for your workflow.';
    card.appendChild(desc);

    // Tags
    const tagsDiv = document.createElement('div');
    tagsDiv.className = 'tags';
    const allTags = [...(tool.categories || []), ...(tool.tags || [])].slice(0, 4);
    allTags.forEach(tag => {
      const tagSpan = document.createElement('span');
      tagSpan.className = 'tag';
      tagSpan.textContent = tag.charAt(0).toUpperCase() + tag.slice(1);
      tagsDiv.appendChild(tagSpan);
    });
    card.appendChild(tagsDiv);

    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'card-actions';

    if (tool.url) {
      const learnBtn = document.createElement('a');
      learnBtn.href = tool.url;
      learnBtn.target = '_blank';
      learnBtn.className = 'btn btn-learn';
      learnBtn.textContent = 'Learn More';
      actions.appendChild(learnBtn);

      const tryBtn = document.createElement('a');
      tryBtn.href = tool.url;
      tryBtn.target = '_blank';
      tryBtn.className = 'btn btn-try';
      tryBtn.textContent = 'Try Tool';
      actions.appendChild(tryBtn);
    } else {
      const infoBtn = document.createElement('button');
      infoBtn.className = 'btn btn-learn';
      infoBtn.textContent = 'More Info';
      infoBtn.disabled = true;
      actions.appendChild(infoBtn);
    }

    card.appendChild(actions);

    // Rating section
    const rateDiv = document.createElement('div');
    rateDiv.className = 'rate-section';

    const input = document.createElement('input');
    input.type = 'number';
    input.min = 1;
    input.max = 10;
    input.placeholder = 'Rate';
    input.title = 'Rate this tool 1-10';

    const btn = document.createElement('button');
    btn.textContent = 'Rate';
    btn.onclick = async () => {
      const val = parseInt(input.value);
      if (!val || val < 1 || val > 10) {
        alert('Please enter a rating between 1 and 10');
        return;
      }
      const payload = { query: q, tool: tool.name, rating: val, details: { from_ui: true } };
      const rsp = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const jr = await rsp.json();
      if (jr.ok) {
        btn.textContent = '✓ Rated';
        btn.disabled = true;
        input.disabled = true;
      } else {
        alert('Failed to save rating');
      }
    };

    rateDiv.appendChild(input);
    rateDiv.appendChild(btn);
    card.appendChild(rateDiv);

    resultsEl.appendChild(card);
  });
}

document.getElementById('searchBtn').addEventListener('click', search);

// allow pressing Enter to search
document.getElementById('query').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') search();
});

// ─────────────────────────────────────────────────────
// Query Reflection — "Here's what I understood"
// Makes the user feel heard before showing results.
// ─────────────────────────────────────────────────────
function buildReflection(query, meta, results) {
  const cap = s => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';

  // Build the narrative pieces
  const intent   = meta.intent;
  const industry = meta.industry;
  const goal     = meta.goal;
  const keywords = (meta.expanded_keywords || []).slice(0, 6);
  const negatives = meta.negatives || [];
  const corrections = meta.corrections || {};
  const suggestions = meta.suggested_questions || [];

  // Compose a human sentence reflecting the query back
  let reflection = '';
  if (intent || goal) {
    reflection = 'I can see you\'re looking for ';
    if (intent && goal && intent !== goal) {
      reflection += `<strong>${cap(intent)}</strong> tools to help with <strong>${cap(goal)}</strong>`;
    } else if (intent) {
      reflection += `<strong>${cap(intent)}</strong> tools`;
    } else if (goal) {
      reflection += `tools to help with <strong>${cap(goal)}</strong>`;
    }
    if (industry) {
      reflection += ` in the <strong>${cap(industry)}</strong> space`;
    }
    reflection += '.';
  } else if (keywords.length > 0) {
    reflection = `Searching for tools related to <strong>${keywords.slice(0, 3).map(cap).join('</strong>, <strong>')}</strong>.`;
  } else {
    reflection = `Here's what I found for "<strong>${query}</strong>".`;
  }

  // How many results
  reflection += ` I found <strong>${results.length} tool${results.length === 1 ? '' : 's'}</strong> that match your needs.`;

  // Build the DOM
  const container = document.createElement('div');
  container.className = 'query-reflection';

  // Main reflection text
  const textP = document.createElement('p');
  textP.className = 'reflection-text';
  textP.innerHTML = reflection;
  container.appendChild(textP);

  // Reasoning chips — show the user which signals the engine picked up
  const signals = [];

  if (intent)   signals.push({ icon: '🎯', label: cap(intent), type: 'intent' });
  if (industry) signals.push({ icon: '🏢', label: cap(industry), type: 'industry' });
  if (goal && goal !== intent) signals.push({ icon: '✦', label: cap(goal), type: 'goal' });

  // Show corrected terms
  const corrKeys = Object.keys(corrections);
  if (corrKeys.length > 0) {
    corrKeys.forEach(k => {
      signals.push({ icon: '✏️', label: `${k} → ${corrections[k]}`, type: 'correction' });
    });
  }

  // Show excluded terms
  if (negatives.length > 0) {
    negatives.forEach(n => {
      signals.push({ icon: '🚫', label: cap(n), type: 'negative' });
    });
  }

  // Extra keyword signals the user might not have typed explicitly
  const mainTerms = new Set([intent, industry, goal].filter(Boolean).map(s => s.toLowerCase()));
  keywords.filter(k => !mainTerms.has(k.toLowerCase())).slice(0, 4).forEach(k => {
    signals.push({ icon: '🔗', label: cap(k), type: 'keyword' });
  });

  if (signals.length > 0) {
    const chipsDiv = document.createElement('div');
    chipsDiv.className = 'reflection-chips';
    signals.forEach(s => {
      const chip = document.createElement('span');
      chip.className = 'reflection-chip chip-' + s.type;
      chip.innerHTML = `${s.icon} ${s.label}`;
      chipsDiv.appendChild(chip);
    });
    container.appendChild(chipsDiv);
  }

  // Follow-up suggestions
  if (suggestions.length > 0) {
    const sugDiv = document.createElement('div');
    sugDiv.className = 'reflection-suggestions';
    const sugLabel = document.createElement('span');
    sugLabel.className = 'reflection-suggest-label';
    sugLabel.textContent = 'Refine your search:';
    sugDiv.appendChild(sugLabel);
    suggestions.slice(0, 2).forEach(s => {
      const btn = document.createElement('button');
      btn.className = 'reflection-suggest-btn';
      btn.textContent = s;
      btn.onclick = () => {
        document.getElementById('query').value = s;
        search();
      };
      sugDiv.appendChild(btn);
    });
    container.appendChild(sugDiv);
  }

  return container;
}
