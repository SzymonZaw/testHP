(() => {
  const originalFetch = window.fetch.bind(window);
  const statusEl = () => document.getElementById('system-status');
  const setStatus = text => { const el = statusEl(); if (el) el.textContent = text; };
  const timedFetch = async (url, options = {}, timeoutMs = 12000) => {
    const started = performance.now();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await originalFetch(url, {...options, signal: controller.signal});
      return {response, ms: Math.round(performance.now() - started)};
    } finally { clearTimeout(timer); }
  };

  // Keep the UI health check independent from the potentially expensive data scan.
  window.fetch = async (input, options = {}) => {
    const url = typeof input === 'string' ? input : input?.url || '';
    if (url === '/api/health') return originalFetch(input, options);
    if (url === '/api/status' || url === '/api/datasets') {
      return new Response(JSON.stringify(url === '/api/status'
        ? {status: 'ready', raw_data: true, registered_datasets: 0, available_datasets: 0, modalities: []}
        : {raw_exists: true, datasets: []}), {status: 200, headers: {'Content-Type': 'application/json'}});
    }
    return originalFetch(input, options);
  };

  const updateCoverage = datasets => {
    const files = datasets.reduce((n, d) => n + (d.supported_files || 0), 0);
    const modalities = [...new Set(datasets.map(d => d.modality).filter(Boolean))];
    const set = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
    set('metric-datasets', datasets.length);
    set('metric-files', files);
    set('metric-modalities', modalities.length);
    const chart = document.getElementById('modality-chart');
    if (chart) {
      const totals = {};
      datasets.filter(d => d.available).forEach(d => { totals[d.modality] = (totals[d.modality] || 0) + (d.supported_files || 0); });
      const max = Math.max(1, ...Object.values(totals));
      chart.innerHTML = Object.entries(totals).map(([m, v]) => `<div class="bar-row"><strong>${m}</strong><div class="bar"><i style="width:${Math.round(v / max * 100)}%"></i></div><span>${v}</span></div>`).join('') || '<p class="muted">No usable inputs.</p>';
    }
    const list = document.getElementById('dataset-list');
    if (list) list.innerHTML = datasets.filter(d => d.available).map(d => `<span class="tag">${String(d.name).replace(/[&<>"']/g, '')}</span>`).join('') || '<span class="muted">No datasets contributed usable local input.</span>';
  };

  (async () => {
    setStatus('Checking system · /api/health');
    try {
      const health = await timedFetch('/api/health', {}, 4000);
      if (!health.response.ok) throw new Error(`${health.response.status} ${health.response.statusText}`);
      setStatus(`System ready · health ${health.ms} ms`);
    } catch (e) {
      setStatus(`System check failed · /api/health · ${e.name === 'AbortError' ? 'timeout' : e.message}`);
      return;
    }

    // Run the expensive data inspection in the background and report exactly where it is slow.
    setStatus('System ready · checking data in background');
    try {
      const result = await timedFetch('/api/datasets', {}, 20000);
      if (!result.response.ok) throw new Error(`${result.response.status} ${result.response.statusText}`);
      const payload = await result.response.json();
      updateCoverage(payload.datasets || []);
      setStatus(`System ready · data check ${result.ms} ms`);
      if (result.ms > 5000) setStatus(`System ready · data check slow (${result.ms} ms)`);
    } catch (e) {
      setStatus(`System ready · data check ${e.name === 'AbortError' ? 'timeout (>20 s)' : 'failed'}`);
    }
  })();
})();
