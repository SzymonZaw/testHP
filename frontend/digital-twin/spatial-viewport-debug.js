(() => {
  const boot = () => {
    const canvas = document.getElementById('twin-canvas');
    if (!canvas) return;

    let minimized = true;
    let started = Date.now();
    let lastError = null;
    let lastNavigation = null;
    let lastInteraction = null;
    let lastStateRequest = null;
    let lastStatePayload = null;
    let lastObservationsPayload = null;
    let stateRequestSeq = 0;

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    if (host.parentElement !== document.body) document.body.appendChild(host);
    Object.assign(host.style, {
      position: 'fixed', right: '16px', bottom: '16px', zIndex: '2147483647',
      width: 'min(620px,calc(100vw - 32px))', pointerEvents: 'auto', isolation: 'isolate'
    });

    let toggle = document.getElementById('twin-debug-toggle');
    if (!toggle) {
      toggle = document.createElement('button');
      toggle.id = 'twin-debug-toggle';
      toggle.type = 'button';
      host.appendChild(toggle);
    }
    Object.assign(toggle.style, {
      display: 'block', padding: '8px 12px', borderRadius: '8px',
      border: '1px solid #4b746b', background: '#0b1514', color: '#9bd8c4',
      font: '800 11px ui-monospace,SFMono-Regular,Consolas,monospace',
      cursor: 'pointer', pointerEvents: 'auto'
    });

    let panel = document.getElementById('twin-debug-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'twin-debug-panel';
      panel.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
          <strong>TWIN VIEWPORT · DEBUG</strong>
          <button id="twin-debug-close" type="button">MINIMIZE</button>
        </div>
        <pre id="twin-debug-runtime"></pre>
        <pre id="twin-debug-state"></pre>
        <pre id="twin-debug-evidence"></pre>
        <pre id="twin-debug-errors"></pre>`;
      host.appendChild(panel);
    }
    Object.assign(panel.style, {
      display: 'none', marginTop: '6px', maxHeight: '680px', overflow: 'auto',
      padding: '12px', boxSizing: 'border-box', borderRadius: '10px',
      background: 'rgba(5,12,13,.98)', border: '1px solid #4b746b',
      boxShadow: '0 12px 35px rgba(0,0,0,.55)', color: '#dcece6',
      font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace',
      pointerEvents: 'auto'
    });

    const runtime = document.getElementById('twin-debug-runtime');
    const state = document.getElementById('twin-debug-state');
    const evidence = document.getElementById('twin-debug-evidence');
    const errors = document.getElementById('twin-debug-errors');
    if (!runtime || !state || !evidence || !errors) return;

    const readState = () => {
      const manager = window.spatialViewportManager;
      const node = document.getElementById('spatial-node');
      const badge = document.getElementById('spatial-level-badge');
      const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')]
        .map(x => x.textContent.trim()).filter(Boolean);
      const children = [...document.querySelectorAll('#spatial-children .spatial-target')]
        .map(x => ({
          label: x.querySelector('strong')?.textContent?.trim() || x.textContent.trim(),
          id: x.dataset?.spatialId || x.getAttribute('data-spatial-id') || null,
          disabled: !!x.disabled,
          connected: x.isConnected
        }));
      return {
        manager: !!manager,
        level: badge?.textContent?.trim() || '?',
        target: node?.querySelector('strong')?.textContent?.trim() || '?',
        path: breadcrumb.join(' > ') || '(root)',
        children,
        renderer: manager?.active?.constructor?.name || 'none',
        activeKey: manager?.activeKey || 'none',
        evidenceTarget: window.spatialEvidenceTarget || null,
        selectedSpatialNode: window.selectedSpatialNode || null
      };
    };

    const getSpatialId = detail => {
      if (detail?.spatial_id) return String(detail.spatial_id);
      if (detail?.id) return String(detail.id);
      const current = readState();
      const target = current.evidenceTarget;
      if (typeof target === 'string' && target) return target;
      return 'hand/palm';
    };

    const refreshEvidenceDiagnostics = async detail => {
      const spatialId = getSpatialId(detail);
      const seq = ++stateRequestSeq;
      const params = new URLSearchParams({
        subject_id: 'own_cohort',
        timepoint: 'T0',
        spatial_id: spatialId,
        include_descendants: 'true'
      });
      const url = `/api/biological-state?${params.toString()}`;
      const observationsUrl = `/api/observations?subject_id=own_cohort&timepoint=T0&include_archived=false`;
      const startedAt = performance.now();
      lastStateRequest = { seq, spatialId, url, startedAt: new Date().toISOString() };
      try {
        const [stateResponse, observationsResponse] = await Promise.all([
          fetch(url, { cache: 'no-store' }),
          fetch(observationsUrl, { cache: 'no-store' })
        ]);
        const stateText = await stateResponse.text();
        const observationsText = await observationsResponse.text();
        let statePayload = null;
        let observationsPayload = null;
        try { statePayload = JSON.parse(stateText); } catch (_) {}
        try { observationsPayload = JSON.parse(observationsText); } catch (_) {}
        if (seq !== stateRequestSeq) return;
        lastStatePayload = statePayload;
        lastObservationsPayload = observationsPayload;
        lastStateRequest = {
          ...lastStateRequest,
          completedAt: new Date().toISOString(),
          durationMs: Math.round(performance.now() - startedAt),
          http: stateResponse.status,
          ok: stateResponse.ok,
          observationsHttp: observationsResponse.status,
          observationsOk: observationsResponse.ok
        };
      } catch (error) {
        if (seq !== stateRequestSeq) return;
        lastStatePayload = null;
        lastObservationsPayload = null;
        lastStateRequest = {
          ...lastStateRequest,
          completedAt: new Date().toISOString(),
          durationMs: Math.round(performance.now() - startedAt),
          error: error?.message || String(error)
        };
      }
      render();
    };

    const render = () => {
      if (minimized) return;
      const s = readState();
      const statePayload = lastStatePayload || {};
      const summary = statePayload.summary || {};
      const apiState = statePayload.state || {};
      const observations = Array.isArray(lastObservationsPayload?.observations)
        ? lastObservationsPayload.observations : [];
      const scopedIds = new Set((apiState.evidence_ids || []).map(String));
      const scopedObservationIds = new Set(observations.filter(o => scopedIds.has(String(o.evidence_id))).map(o => String(o.id)));
      const relevantObservations = observations.filter(o => scopedObservationIds.has(String(o.id)));

      runtime.textContent = [
        'RUNTIME',
        `status:       ${window.__testhpTwinReady ? 'READY' : 'INITIALIZING'}`,
        `init age:     ${Date.now() - started} ms`,
        `manager:      ${s.manager ? 'present' : 'missing'}`,
        `canvas:       ${canvas.width}×${canvas.height}`,
        `last API:     ${lastStateRequest ? `${lastStateRequest.http ?? '—'} · ${lastStateRequest.durationMs ?? '—'} ms` : '(none)'}`
      ].join('\n');

      state.textContent = [
        '', 'SPATIAL STATE',
        `level:        ${s.level}`,
        `target:       ${s.target}`,
        `path:         ${s.path}`,
        `evidence id:  ${s.evidenceTarget ? JSON.stringify(s.evidenceTarget) : '(none)'}`,
        `selected node:${s.selectedSpatialNode ? ` ${JSON.stringify(s.selectedSpatialNode)}` : ' (none)'}`,
        `children:     ${s.children.map(c => `${c.label}[${c.id || '?'}${c.disabled ? ',disabled' : ''}]`).join(' | ') || '(none)'}`,
        `renderer:     ${s.renderer}`,
        `active key:   ${s.activeKey}`,
        '', 'LAST NAVIGATION',
        lastNavigation ? JSON.stringify(lastNavigation, null, 2) : '(none)'
      ].join('\n');

      evidence.textContent = [
        '', 'BIOLOGICAL STATE · EVIDENCE SCOPE',
        `request:      ${lastStateRequest?.url || '(none)'}`,
        `include desc: ${summary.include_descendants === true ? 'YES' : 'NO'}`,
        `scope:        ${summary.scope || s.evidenceTarget || '(none)'}`,
        `API status:   ${lastStateRequest?.ok ? 'OK' : lastStateRequest ? 'FAILED' : 'NOT RUN'}`,
        `state count:  ${apiState.evidence_count ?? '—'}`,
        `observations: ${summary.observations ?? '—'}`,
        `direct:       ${summary.direct_evidence ?? '—'}`,
        `descendants:  ${summary.descendant_evidence ?? '—'}`,
        `availability: ${apiState.availability ?? '—'}`,
        `confidence:   ${apiState.confidence?.value ?? '—'}`,
        `evidence ids: ${(apiState.evidence_ids || []).join(' | ') || '(none)'}`,
        `by location:  ${Array.isArray(summary.by_location) && summary.by_location.length ? summary.by_location.map(x => `${x.name || x.spatial_id}=${x.count}`).join(' · ') : '(none)'}`,
        '', 'OBSERVATIONS IN GLOBAL REGISTRY',
        `total:        ${lastObservationsPayload?.count ?? observations.length}`,
        `scoped:       ${relevantObservations.length}`,
        relevantObservations.length
          ? relevantObservations.map(o => `${o.id} | spatial=${o.spatial_id} | level=${o.biological_level} | evidence=${o.evidence_id || '(none)'}`).join('\n')
          : '(no observations matched returned evidence ids)',
        '', 'DIAGNOSTIC HINT',
        apiState.evidence_count === 0
          ? 'Wybrany region nie dostał evidence z API. Sprawdź spatial_id, parent_id oraz zgodność hierarchii lokalizacji.'
          : `API zwraca ${apiState.evidence_count} evidence; jeśli UI pokazuje inną liczbę, problem jest po stronie synchronizacji/renderowania UI.`
      ].join('\n');

      errors.textContent = [
        '', 'ERROR / INTERACTION',
        `last error:   ${lastError || '(none)'}`,
        `last input:   ${lastInteraction ? JSON.stringify(lastInteraction) : '(none)'}`,
        `last request: ${lastStateRequest ? JSON.stringify(lastStateRequest, null, 2) : '(none)'}`
      ].join('\n');
    };

    window.addEventListener('error', e => {
      lastError = `${e.message || 'unknown'} | ${e.filename || ''}:${e.lineno || ''}`;
      render();
    });
    window.addEventListener('unhandledrejection', e => {
      lastError = String(e.reason?.stack || e.reason || 'Unhandled promise rejection');
      render();
    });
    window.addEventListener('testhp:twin-error', e => { lastError = JSON.stringify(e.detail || {}); render(); });
    window.addEventListener('testhp:spatial-layer-changed', e => {
      lastNavigation = e.detail || {};
      refreshEvidenceDiagnostics(e.detail || {});
    });
    window.addEventListener('testhp:spatial-change', e => {
      lastNavigation = e.detail || {};
      refreshEvidenceDiagnostics(e.detail || {});
    });
    window.addEventListener('testhp:viewport-rendered', e => {
      lastNavigation = e.detail || {};
      refreshEvidenceDiagnostics(e.detail || {});
    });

    canvas.addEventListener('click', e => {
      lastInteraction = { type: 'canvas click', x: Math.round(e.clientX), y: Math.round(e.clientY) };
      render();
    }, { passive: true });

    document.addEventListener('click', e => {
      const target = e.target?.closest?.('.spatial-target,#spatial-breadcrumb button');
      if (!target) return;
      lastInteraction = {
        type: 'spatial navigation click',
        label: target.textContent?.trim() || '',
        spatialId: target.dataset?.spatialId || target.getAttribute('data-spatial-id') || null,
        disabled: !!target.disabled,
        time: new Date().toISOString()
      };
      setTimeout(() => refreshEvidenceDiagnostics(readState()), 0);
    }, true);

    const setMinimized = value => {
      minimized = value;
      panel.style.display = minimized ? 'none' : 'block';
      toggle.textContent = minimized ? 'TWIN VIEWPORT DEBUG · ROZWIŃ' : 'TWIN VIEWPORT DEBUG · ZWIŃ';
      if (!minimized) {
        render();
        refreshEvidenceDiagnostics(readState());
      }
    };

    toggle.onclick = () => setMinimized(!minimized);
    document.getElementById('twin-debug-close')?.addEventListener('click', () => setMinimized(true));
    setMinimized(true);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
