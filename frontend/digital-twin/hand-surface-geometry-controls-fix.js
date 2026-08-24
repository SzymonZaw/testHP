(() => {
  const DEFAULT = Object.freeze({
    palmLength: 1,
    palmWidth: 1,
    thickness: 1,
    fingerSpread: 1,
    taper: 1,
    thumbAngle: 1,
  });

  const stateOf = () => ({
    ...DEFAULT,
    ...(window.digitalTwinGeometry?.getState?.() || {}),
  });

  const same = (a, b) => Object.keys(DEFAULT).every(
    key => Number(a?.[key] ?? 1) === Number(b?.[key] ?? 1)
  );

  const removeQuickStart = () => {
    const groups = [...document.querySelectorAll('.hss-geometry-group')];
    let removed = false;
    groups.forEach(group => {
      const text = (group.textContent || '').replace(/\s+/g, ' ').trim();
      if (/^Szybki start/i.test(text)) {
        group.remove();
        removed = true;
      }
    });
    document.querySelectorAll('.hss-preset').forEach(el => {
      el.remove();
      removed = true;
    });
    return removed;
  };

  const syncUi = geometry => {
    const g = { ...DEFAULT, ...geometry };
    document.querySelectorAll('.hss-geometry-number[data-value-for]').forEach(input => {
      const key = input.dataset.valueFor;
      if (key in g) input.value = Number(g[key]).toFixed(2);
    });
    document.querySelectorAll('.hss-geometry-value[data-value-for]').forEach(label => {
      const key = label.dataset.valueFor;
      if (key in g) label.textContent = `${Number(g[key]).toFixed(2)}×`;
    });
    document.querySelectorAll('input[type="range"][data-g]').forEach(input => {
      const key = input.dataset.g;
      if (key in g) input.value = String(g[key]);
    });
  };

  const install = () => {
    if (window.__testhpGeometryControlsFixInstalled) return true;
    const api = window.digitalTwinGeometry;
    if (!api?.getState || !api?.setState) return false;

    window.__testhpGeometryControlsFixInstalled = true;

    let history = [stateOf()];
    let historyIndex = 0;
    let syncing = false;

    const push = geometry => {
      const next = stateOf();
      if (same(history[historyIndex], next)) return;
      history = history.slice(0, historyIndex + 1);
      history.push({ ...next });
      historyIndex = history.length - 1;
    };

    const apply = geometry => {
      syncing = true;
      try {
        const result = api.setState({ ...DEFAULT, ...geometry });
        syncUi(result?.geometry || geometry);
        return result;
      } finally {
        syncing = false;
      }
    };

    const undo = event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (historyIndex <= 0) return;
      historyIndex -= 1;
      apply(history[historyIndex]);
    };

    const redo = event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      if (historyIndex >= history.length - 1) return;
      historyIndex += 1;
      apply(history[historyIndex]);
    };

    const reset = event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      const current = stateOf();
      if (same(current, DEFAULT)) return;
      history = history.slice(0, historyIndex + 1);
      history.push({ ...DEFAULT });
      historyIndex = history.length - 1;
      apply(DEFAULT);
    };

    document.addEventListener('click', event => {
      const target = event.target?.closest?.('button');
      if (!target) return;
      if (target.id === 'hss-geometry-undo') return undo(event);
      if (target.id === 'hss-geometry-redo') return redo(event);
      if (target.id === 'hss-geometry-reset') return reset(event);
    }, true);

    document.addEventListener('input', event => {
      if (syncing) return;
      const input = event.target?.closest?.('input[type="range"][data-g]');
      if (!input) return;
      requestAnimationFrame(() => {
        if (!syncing) push(stateOf());
      });
    });

    const observer = new MutationObserver(() => {
      removeQuickStart();
      syncUi(stateOf());
    });
    if (document.body) observer.observe(document.body, { childList: true, subtree: true });

    removeQuickStart();
    syncUi(stateOf());
    console.info('[geometry-controls-fix] installed: undo/redo/reset use live geometry owner');
    return true;
  };

  const boot = () => {
    if (install()) return;
    setTimeout(boot, 50);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
