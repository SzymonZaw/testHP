(() => {
  const status = document.getElementById('system-status');
  if (!status) return;
  const originalFetch = window.fetch.bind(window);
  const pending = new Map();
  const started = performance.now();
  let ticker = null;
  const seconds = ms => `${(ms / 1000).toFixed(1)} s`;
  const setStatus = text => { status.textContent = text; status.title = text; };
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
    ensureTicker();
    setStatus(`Checking system · ${path} · 0.0 s`);
    try {
      const response = await originalFetch(...args);
      const elapsed = performance.now() - t;
      pending.delete(path);
      if (!pending.size) { clearInterval(ticker); ticker = null; }
      if (!response.ok) setStatus(`Checking system · ${path} returned ${response.status} · ${seconds(elapsed)}`);
      else if (pending.size) setStatus(`Checking system · ${pending.keys().next().value} pending · ${seconds(performance.now() - started)}`);
      else setStatus(`System ready · checks completed in ${seconds(performance.now() - started)}`);
      return response;
    } catch (error) {
      const elapsed = performance.now() - t;
      pending.delete(path);
      if (!pending.size) { clearInterval(ticker); ticker = null; }
      setStatus(`Checking system · ${path} failed after ${seconds(elapsed)}: ${error?.message || error}`);
      throw error;
    }
  };
})();
