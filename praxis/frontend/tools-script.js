async function loadAllTools() {
  const el = document.getElementById('tools');
  el.innerHTML = '<p style="color:rgba(255,255,255,0.4)">Loading tools…</p>';

  try {
    let allTools = [];
    let skip = 0;
    const limit = 50;

    // Paginate through all tools
    while (true) {
      const res = await fetch(`/tools?skip=${skip}&limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Handle both { items: [...] } envelope and plain array
      const items = Array.isArray(data) ? data : (data.items || []);
      allTools = allTools.concat(items);

      // If we got fewer than limit, we've reached the end
      if (items.length < limit) break;
      skip += limit;
    }

    el.innerHTML = '';

    if (!allTools.length) {
      el.textContent = 'No tools available.';
      return;
    }

    allTools.forEach(t => {
      const d = document.createElement('div');
      d.className = 'tool';

      const h = document.createElement('h3');
      h.textContent = t.name;
      d.appendChild(h);

      if (t.description) {
        const desc = document.createElement('p');
        desc.className = 'desc';
        desc.textContent = t.description;
        d.appendChild(desc);
      }

      const meta = document.createElement('div');
      meta.className = 'meta';
      const cats = (t.categories || []).join(', ');
      const tags = (t.tags || []).slice(0, 5).join(', ');
      meta.textContent = `${cats}${tags ? ' · ' + tags : ''}`;
      d.appendChild(meta);

      if (t.url) {
        const a = document.createElement('a');
        a.href = t.url;
        a.target = '_blank';
        a.rel = 'noopener';
        a.className = 'btn';
        a.textContent = 'Visit →';
        d.appendChild(a);
      }

      el.appendChild(d);
    });

    // Update heading with count
    const heading = document.querySelector('.content h2');
    if (heading) heading.textContent = `All Tools (${allTools.length})`;

  } catch (e) {
    console.error('Failed to load tools:', e);
    el.innerHTML = '<p style="color:#ef4444">Failed to load tools. Check console.</p>';
  }
}

loadAllTools();
