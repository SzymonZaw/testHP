(() => {
  const status = document.getElementById('system-status');
  if (!status) return;

  const originalFetch = window.fetch.bind(window);
  const pending = new Map();
  const started = performance.now();
  let ticker = null;
  let dashboardRequestsSeen = 0;
  let healthFinished = false;
  let dashboardScriptLoaded = false;
  let lastPhase = 'system-check loaded';
  const details = [];

  const seconds = ms => `${(ms / 1000).toFixed(1)} s`;
  const addDetail = message => {
    details.push(`[${seconds(performance.now() - started)}] ${message}`);
    while (details.length > 8) details.shift();
    const text = details.join('\n');
    status.title = text;
    status.dataset.diagnostics = text;
  };
  const setStatus = (text, detail = '') => {
    status.textContent = text;
    if (detail) addDetail(detail);
    else status.title = details.join('\n') || text;
  };

  addDetail('system-check.js started');

  window.addEventListener('error', event => {
    const message = event?.error?.message || event?.message || 'Unknown frontend error';
    const file = event?.filename || 'unknown file';
    const shortFile = file.split('/').pop() || file;
    const line = event?.lineno ? `:${event.lineno}:${event.colno || 0}` : '';
    const stack = event?.error?.stack ? ` Stack: ${event.error.stack.split('\n').slice(0, 2).join(' | ')}` : '';
    addDetail(`JS error in ${shortFile}${line}: ${message}${stack}`);
    setStatus(`Checking system · frontend error in ${shortFile}${line}: ${message}`);
  });

  window.addEventListener('unhandledrejection', event => {
    const reason = event?.reason?.message || String(event?.reason || 'Unknown promise rejection');
    addDetail(`Unhandled promise rejection: ${reason}`);
    setStatus(`Checking system · frontend promise error: ${reason}`);
  });

  window.addEventListener('load', () => {
    addDetail(`window load fired; dashboard requests seen: ${dashboardRequestsSeen}`);
  });

  function ensureTicker() {
    if (ticker) return;
    ticker = setInterval(() => {
      if (!pending.size) return;
      const [url, t] = pending.entries().next().value;
      setStatus(`Checking system · waiting for ${url} · ${seconds(performance.now() - t)}`);
    }, 500);
  }

  window.fetch = async (...args) => {
    const input = args[0];
    const raw = typeof input === 'string' ? input : input?.url || String(input);
    const path = (() => { try { return new URL(raw, location.href).pathname; } catch { return raw; } })();
    const t = performance.now();
    pending.set(path, t);
    if (path === '/api/status' || path === '/api/datasets') dashboardRequestsSeen += 1;
    ensureTicker();
    addDetail(`fetch started: ${path}`);
    setStatus(`Checking system · ${path} · 0.0 s`);
    try {
      const response = await originalFetch(...args);
      const elapsed = performance.now() - t;
      pending.delete(path);
      addDetail(`fetch completed: ${path} → HTTP ${response.status} in ${seconds(elapsed)}`);
      if (!pending.size) { clearInterval(ticker); ticker = null; }
      if (!response.ok) setStatus(`Checking system · ${path} returned ${response.status} · ${seconds(elapsed)}`);
      else if (pending.size) setStatus(`Checking system · ${pending.keys().next().value} pending · ${seconds(performance.now() - started)}`);
      else if (healthFinished) setStatus(`System ready · checks completed in ${seconds(performance.now() - started)}`);
      return response;
    } catch (error) {
      const elapsed = performance.now() - t;
      pending.delete(path);
      const message = error?.message || String(error);
      addDetail(`fetch failed: ${path} after ${seconds(elapsed)}: ${message}`);
      if (!pending.size) { clearInterval(ticker); ticker = null; }
      setStatus(`Checking system · ${path} failed after ${seconds(elapsed)}: ${message}`);
      throw error;
    }
  };

  async function runHealthCheck() {
    lastPhase = 'backend health check';
    addDetail('health check started: /api/status + /api/datasets');
    setStatus('Checking system · backend health…');
    try {
      const healthStarted = performance.now();
      const [statusResponse, datasetsResponse] = await Promise.all([
        originalFetch('/api/status'),
        originalFetch('/api/datasets')
      ]);
      const elapsed = performance.now() - healthStarted;
      addDetail(`/api/status → HTTP ${statusResponse.status}; /api/datasets → HTTP ${datasetsResponse.status}; health time ${seconds(elapsed)}`);
      if (!statusResponse.ok) throw new Error(`/api/status returned ${statusResponse.status}`);
      if (!datasetsResponse.ok) throw new Error(`/api/datasets returned ${datasetsResponse.status}`);
      const backend = await statusResponse.json();
      const datasets = await datasetsResponse.json();
      const count = Array.isArray(datasets?.datasets) ? datasets.datasets.length : 0;
      healthFinished = true;
      if (!dashboardRequestsSeen) {
        lastPhase = 'waiting for dashboard script';
        setStatus(`Backend ready · ${count} datasets · dashboard checks not started`);
        addDetail(`backend OK; ${count} datasets; no dashboard API fetch observed yet`);
      } else {
        lastPhase = 'checks completed';
        setStatus(`System ready · backend OK · ${count} datasets · ${seconds(performance.now() - started)}`);
      }
      if (backend?.status && backend.status !== 'ready') {
        addDetail(`backend reported status=${backend.status}`);
        setStatus(`Checking system · backend status: ${backend.status}`);
      }
    } catch (error) {
      healthFinished = true;
      lastPhase = 'backend health check failed';
      const message = error?.message || String(error);
      addDetail(`health check failed: ${message}`);
      setStatus(`Checking system · backend check failed: ${message}`);
    }
  }

  // Detect the common case where app4.js fails during parsing/execution and therefore
  // never starts its own dashboard requests.
  setTimeout(() => {
    if (healthFinished && !dashboardRequestsSeen) {
      addDetail(`dashboard still inactive after 2.0 s; last phase: ${lastPhase}; app4.js may have a syntax/runtime error or did not initialize`);
      setStatus(`Backend ready · dashboard did not initialize · inspect diagnostics`);
    }
  }, 2000);

  runHealthCheck();
})();
