(() => {
  const LEVELS = ['macro', 'tissue', 'cellular', 'molecular'];

  const boot = () => {
    const canvas = document.getElementById('twin-canvas');
    if (!canvas) return;

    let minimized = true;
    const started = Date.now();
    let lastError = null;
    let lastNavigation = null;
    let lastInteraction = null;
    let lastStateRequest = null;
    let lastStatePayload = null;
    let lastObservationsPayload = null;
    let requestSeq = 0;

    const normalize = value => typeof value === 'string'
      ? value.replace(/^\/+|\/+$/g, '')
      : '';

    const levelKey = value => String(value || '?')
      .toLowerCase()
      .replace(/^anatomia\s+/, '')
      .replace('tkanka', 'tissue')
      .replace('komórkowe', 'cellular')
      .replace('komórkowa', 'cellular')
      .replace('molekularne', 'molecular')
      .replace('makro', 'macro')
      .replace('tissue field', 'tissue')
      .replace('cell field', 'cellular');

    const parseCount = value => Number(String(value || '').match(/\d+/)?.[0] || 0);

    let host = document.getElementById('twin-viewport-debug-host');
    if (!host) host = document.createElement('section');
    host.id = 'twin-viewport-debug-host';
    if (host.parentElement !== document.body) document.body.appendChild(host);
    Object.assign(host.style, {
      position: 'fixed', right: '16px', bottom: '16px', zIndex: '2147483647',
      width: 'min(760px,calc(100vw - 32px))', pointerEvents: 'auto', isolation: 'isolate'
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
      display: 'none', marginTop: '6px', maxHeight: '820px', overflow: 'auto',
      padding: '12px', boxSizing: 'border-box', borderRadius: '10px',
      background: 'rgba(5,12,13,.98)', border: '1px solid #4b746b',
      boxShadow: '0 12px 35px rgba(0,0,0,.55)', color: '#dcece6',
      font: '11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace', pointerEvents: 'auto'
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
          id: normalize(x.dataset?.spatialId || x.getAttribute('data-spatial-id') || ''),
          disabled: !!x.disabled,
          connected: x.isConnected,
          tag: x.dataset?.spatialLevel || x.getAttribute('data-spatial-level') || null
        }));
      const selected = window.selectedSpatialNode;
      return {
        manager: !!manager,
        level: badge?.textContent?.trim() || '?',
        target: node?.querySelector('strong')?.textContent?.trim() || '?',
        path: breadcrumb.join(' > ') || '(root)',
        children,
        renderer: manager?.active?.constructor?.name || 'none',
        activeKey: manager?.activeKey || 'none',
        spatialEvidenceTarget: normalize(window.spatialEvidenceTarget || ''),
        selectedSpatialNode: selected || null,
        selectedSpatialId: normalize(selected?.spatial_id || selected?.id || window.spatialEvidenceTarget || '')
      };
    };

    const getSpatialId = detail => normalize(
      detail?.spatial_id || detail?.id || readState().selectedSpatialId || 'hand'
    );

    const fetchDiagnostics = async detail => {
      const spatialId = getSpatialId(detail);
      const seq = ++requestSeq;
      const params = new URLSearchParams({
        subject_id: 'own_cohort',
        timepoint: 'T0',
        spatial_id: spatialId,
        include_descendants: 'true'
      });
      const url = `/api/biological-state?${params.toString()}`;
      const observationsUrl = '/api/observations?subject_id=own_cohort&timepoint=T0&include_archived=false';
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
        if (seq !== requestSeq) return;
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
        if (seq !== requestSeq) return;
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
      const ui = readState();
      const payload = lastStatePayload || {};
      const summary = payload.summary || {};
      const apiState = payload.state || {};
      const rawObservations = Array.isArray(lastObservationsPayload?.observations)
        ? lastObservationsPayload.observations : [];
      const selected = normalize(lastStateRequest?.spatialId || ui.selectedSpatialId || '');

      const observations = rawObservations.map(item => ({
        id: String(item.id || ''),
        spatial: normalize(item.spatial_id),
        level: item.biological_level || '?',
        levelKey: levelKey(item.biological_level),
        evidence: item.evidence_id ? String(item.evidence_id) : null,
        subject: item.subject_id || '?',
        timepoint: item.timepoint || item.timepoint_id || '?',
        archived: !!item.archived,
        modality: item.modality || null,
        source: item.source || null,
        name: item.name || null,
        value: item.value,
        status: item.status || null,
        version: item.version ?? null
      }));

      const direct = observations.filter(o => o.spatial === selected);
      const descendants = selected
        ? observations.filter(o => o.spatial.startsWith(`${selected}/`))
        : [];
      const ancestors = selected
        ? selected.split('/').map((_, index) => selected.split('/').slice(0, index + 1).join('/'))
        : [];
      const siblings = observations.filter(o => {
        if (!selected || !o.spatial || o.spatial === selected) return false;
        const parts = o.spatial.split('/');
        const selectedParts = selected.split('/');
        return parts.length === selectedParts.length && parts.slice(0, -1).join('/') === selectedParts.slice(0, -1).join('/');
      });
      const ancestorObservations = observations.filter(o => ancestors.slice(0, -1).includes(o.spatial));
      const scoped = direct.concat(descendants);

      const byLocation = {};
      const byLevel = {};
      const scopedByLevel = {};
      observations.forEach(o => {
        const key = o.spatial || '(missing spatial_id)';
        byLocation[key] = (byLocation[key] || 0) + 1;
        byLevel[o.levelKey] = (byLevel[o.levelKey] || 0) + 1;
      });
      scoped.forEach(o => {
        scopedByLevel[o.levelKey] = (scopedByLevel[o.levelKey] || 0) + 1;
      });

      const apiEvidenceIds = new Set((apiState.evidence_ids || []).map(String));
      const scopedWithEvidence = scoped.filter(o => o.evidence && apiEvidenceIds.has(o.evidence));
      const scopedWithoutEvidence = scoped.filter(o => !o.evidence || !apiEvidenceIds.has(o.evidence));

      const inspector = {
        title: document.getElementById('region-title')?.textContent?.trim() || '?',
        context: document.getElementById('region-context')?.textContent?.trim() || '?',
        counts: Object.fromEntries(LEVELS.map(level => [
          level, document.getElementById(`${level}-state`)?.textContent?.trim() || ''
        ])),
        evidenceRows: [...document.querySelectorAll('.evidence-row')].map(row => ({
          layer: row.querySelector('.layer')?.textContent?.trim() || '?',
          title: row.querySelector('strong')?.textContent?.trim() || '?',
          detail: row.querySelector('p')?.textContent?.trim() || ''
        })),
        interpretationCount: document.getElementById('evidence-count')?.textContent?.trim() || null,
        interpretationAvailability: document.getElementById('evidence-level')?.textContent?.trim() || null
      };

      const inspectorCounts = Object.fromEntries(
        LEVELS.map(level => [level, parseCount(inspector.counts[level])])
      );
      const layerDiagnostics = LEVELS.map(level => {
        const raw = scoped.filter(o => o.levelKey === level);
        const directLayer = direct.filter(o => o.levelKey === level);
        const descendantLayer = descendants.filter(o => o.levelKey === level);
        const locations = {};
        raw.forEach(o => {
          const key = o.spatial || '(missing spatial_id)';
          locations[key] = (locations[key] || 0) + 1;
        });
        return {
          layer: level,
          inspector: inspectorCounts[level],
          scoped: raw.length,
          direct: directLayer.length,
          descendants: descendantLayer.length,
          locations,
          spatialNodes: Object.keys(locations).length,
          missingSpatial: raw.filter(o => !o.spatial).length
        };
      });

      const sameLayerAcrossNodes = layerDiagnostics
        .filter(x => x.spatialNodes > 1)
        .map(x => `${x.layer}: ${x.scoped} records across ${x.spatialNodes} spatial nodes`);
      const inspectorOnlyLayers = layerDiagnostics
        .filter(x => x.inspector > 0 && x.scoped === 0)
        .map(x => `${x.layer}: inspector=${x.inspector}, scoped=0`);
      const inspectorMismatches = layerDiagnostics
        .filter(x => x.inspector !== x.scoped)
        .map(x => `${x.layer}: inspector=${x.inspector}, scoped=${x.scoped}`);
      const sameLocationDuplicates = layerDiagnostics.map(x => {
        const duplicates = Object.entries(x.locations).filter(([, count]) => count > 1);
        return duplicates.length
          ? `${x.layer}: ${duplicates.map(([id, count]) => `${id}×${count}`).join(', ')}`
          : null;
      }).filter(Boolean);

      const navChildren = ui.children;
      const navChildIds = navChildren.map(child => child.id).filter(Boolean);
      const childObservations = observations.filter(o => navChildIds.includes(o.spatial));
      const childSubtreeObservations = observations.filter(o => navChildIds.some(id => o.spatial === id || o.spatial.startsWith(`${id}/`)));

      const moduleScopes = {
        model: normalize(ui.selectedSpatialId),
        navigation: normalize(ui.selectedSpatialId),
        inspector: selected,
        observations: selected,
        interpretation: selected,
        api: normalize(summary.scope || lastStateRequest?.spatialId)
      };
      const moduleScopeValues = Object.values(moduleScopes).filter(Boolean);
      const allModulesAgree = moduleScopeValues.length > 0 && moduleScopeValues.every(value => value === selected);

      const interpretationUiCount = inspector.interpretationCount === null ? null : parseCount(inspector.interpretationCount);
      const observationCount = Number(summary.observation_count ?? summary.observations ?? apiState.observation_count ?? scoped.length);
      const evidenceCount = Number(apiState.evidence_count ?? summary.explicit_evidence ?? 0);
      const stateCount = Number(apiState.state_count ?? apiState.evidence_count ?? 0);
      const validatedCount = scoped.filter(o => {
        const metadata = rawObservations.find(raw => String(raw.id || '') === o.id)?.validated_interpretations;
        return metadata && typeof metadata === 'object' && Object.keys(metadata).length > 0;
      }).length;

      const semanticIssues = [];
      if (!allModulesAgree) semanticIssues.push('MODULE_SCOPE_MISMATCH');
      if (interpretationUiCount !== null && interpretationUiCount !== observationCount) semanticIssues.push('INTERPRETATION_COUNT_MISMATCH');
      if (observationCount !== scoped.length) semanticIssues.push('API_OBSERVATION_COUNT_MISMATCH');
      if (evidenceCount !== scopedWithEvidence.length) semanticIssues.push('API_EVIDENCE_LINK_MISMATCH');
      if (navChildren.some(child => !child.id)) semanticIssues.push('NAVIGATION_CHILD_WITHOUT_SPATIAL_ID');
      if (sameLayerAcrossNodes.length && inspectorMismatches.length) semanticIssues.push('SAME_LAYER_SCOPE_MISMATCH');

      const resolutionRows = observations.map(o => {
        let spatialRelation = 'OUTSIDE';
        if (o.spatial === selected) spatialRelation = 'DIRECT';
        else if (selected && o.spatial.startsWith(`${selected}/`)) spatialRelation = 'DESCENDANT';
        else if (siblings.some(sibling => sibling.id === o.id)) spatialRelation = 'SIBLING';
        else if (ancestors.includes(o.spatial)) spatialRelation = 'ANCESTOR';
        const subjectMatch = o.subject === 'own_cohort';
        const timeMatch = o.timepoint === 'T0';
        const included = (spatialRelation === 'DIRECT' || spatialRelation === 'DESCENDANT') && subjectMatch && timeMatch && !o.archived;
        return { ...o, spatialRelation, subjectMatch, timeMatch, included };
      });

      const spatialContract = ui.selectedSpatialNode || {};
      const expectedParent = selected ? selected.split('/').slice(0, -1).join('/') || null : null;
      const hierarchyIssues = [];
      navChildren.forEach(child => {
        if (!child.id) hierarchyIssues.push(`child '${child.label}' has no spatial_id`);
        else if (expectedParent && !child.id.startsWith(`${selected}/`)) hierarchyIssues.push(`${child.id} is not a child of ${selected}`);
      });
      if (selected && spatialContract.spatial_id && normalize(spatialContract.spatial_id) !== selected) {
        hierarchyIssues.push(`selectedSpatialNode.spatial_id=${spatialContract.spatial_id} differs from ${selected}`);
      }

      const rawObservationLines = resolutionRows.map(o => [
        `${o.id || '(no id)'}`,
        `spatial=${o.spatial || '(none)'}`,
        `level=${o.level}`,
        `relation=${o.spatialRelation}`,
        `subject=${o.subjectMatch ? 'MATCH' : 'MISMATCH'}`,
        `time=${o.timeMatch ? 'MATCH' : 'MISMATCH'}`,
        `evidence=${o.evidence || '(none)'}`,
        `included=${o.included ? 'YES' : 'NO'}`,
        o.included ? 'reason=scope+subject+time' : `reason=${o.spatialRelation.toLowerCase()}`
      ].join(' | ')).join('\n') || '(none)';

      const moduleScopeLines = Object.entries(moduleScopes)
        .map(([module, value]) => `  ${module.padEnd(15)} ${value || '(none)'}`)
        .join('\n');
      const hierarchyLines = navChildren
        .map(child => `  ${child.label} | id=${child.id || '?'} | type=${child.tag || '?'} | disabled=${child.disabled} | connected=${child.connected}`)
        .join('\n') || '  (none)';
      const layerLines = layerDiagnostics
        .map(x => `  ${x.layer}: inspector=${x.inspector} | scoped=${x.scoped} | direct=${x.direct} | descendants=${x.descendants} | spatial_nodes=${x.spatialNodes} | missing_spatial=${x.missingSpatial}`)
        .join('\n');
      const distributionLines = layerDiagnostics
        .map(x => `  ${x.layer}: ${Object.entries(x.locations).map(([id, count]) => `${id}=${count}`).join(' · ') || '(none)'}`)
        .join('\n');
      const byLocationLines = Object.entries(byLocation).sort().map(([id, count]) => `  ${id} = ${count}`).join('\n') || '  (none)';
      const byLevelLines = Object.entries(byLevel).sort().map(([level, count]) => `  ${level} = ${count}`).join('\n') || '  (none)';
      const scopeLevelLines = LEVELS.map(level => `  ${level}: ${scopedByLevel[level] || 0}`).join('\n');

      let hint = 'No immediate semantic mismatch detected.';
      if (hierarchyIssues.length) hint = 'NAVIGATION HIERARCHY IS INCONSISTENT. Inspect missing/incorrect spatial_id or parent-child links.';
      else if (interpretationUiCount !== null && interpretationUiCount !== observationCount) hint = 'INTERPRETATION COUNT DOES NOT FOLLOW observation_count. Evidence must not be used as the data count.';
      else if (observationCount !== scoped.length) hint = 'API observation_count differs from raw observations resolved from the same scope.';
      else if (evidenceCount === 0 && scoped.length > 0) hint = 'OBSERVATIONS EXIST WITHOUT EVIDENCE. This is valid, but the UI must keep observation availability separate from evidence-backed state.';
      else if (sameLayerAcrossNodes.length) hint = 'SAME BIOLOGICAL LEVEL EXISTS ON MULTIPLE SPATIAL NODES. Verify that spatial_id remains part of the record identity.';
      else if (inspectorMismatches.length) hint = 'INSPECTOR LAYER COUNTS DO NOT MATCH the resolved spatial scope.';

      runtime.textContent = [
        'RUNTIME',
        `status:       ${window.__testhpTwinReady ? 'READY' : 'INITIALIZING'}`,
        `init age:     ${Date.now() - started} ms`,
        `manager:      ${ui.manager ? 'present' : 'missing'}`,
        `canvas:       ${canvas.width}×${canvas.height}`,
        `last API:     ${lastStateRequest ? `${lastStateRequest.http ?? '—'} · ${lastStateRequest.durationMs ?? '—'} ms` : '(none)'}`,
        `semantic issues: ${semanticIssues.length ? semanticIssues.join(', ') : 'NONE'}`
      ].join('\n');

      state.textContent = [
        '', 'SPATIAL CONTRACT',
        `selected id:       ${selected || '(none)'}`,
        `selected label:    ${ui.target}`,
        `selected level:    ${ui.level}`,
        `path:              ${ui.path}`,
        `parent id:         ${spatialContract.parent_id || expectedParent || '(unknown)'}`,
        `location level:    ${spatialContract.location_level || '(unknown)'}`,
        `selected node id:  ${normalize(spatialContract.spatial_id || spatialContract.id) || '(none)'}`,
        '', 'CANONICAL SCOPE',
        `direct rule:       spatial_id === ${selected || '(none)'}`,
        `descendant rule:   spatial_id startsWith ${selected ? `${selected}/` : '(none)'}`,
        `direct:            ${direct.length}`,
        `descendants:       ${descendants.length}`,
        `ancestors:         ${ancestorObservations.length}`,
        `siblings:          ${siblings.length}`,
        `outside scope:     ${Math.max(0, observations.length - scoped.length)}`,
        '', 'MODULE SCOPE COMPARISON',
        moduleScopeLines,
        `  RESULT            ${allModulesAgree ? 'ALL AGREE' : 'MISMATCH'}`,
        '', 'NAVIGATION CONTRACT',
        `children:           ${navChildren.length}`,
        hierarchyLines,
        `hierarchy result:   ${hierarchyIssues.length ? 'FAIL' : 'PASS'}`,
        hierarchyIssues.length ? hierarchyIssues.map(issue => `  ! ${issue}`).join('\n') : '',
        '', 'PARENT / CHILD INTEGRITY',
        `canonical parent:   ${expectedParent || '(root)'}`,
        `orphan candidates:  ${navChildren.filter(child => !child.id).length}`,
        `cycle check:        not inferable from DOM; see spatial model diagnostics`,
        '', 'RAW OBSERVATION LOCATIONS',
        byLocationLines,
        '', 'OBSERVATIONS BY BIOLOGICAL LEVEL',
        byLevelLines,
        '', 'RESOLVED SCOPE BY LEVEL',
        scopeLevelLines
      ].join('\n');

      evidence.textContent = [
        '', 'BIOLOGICAL STATE · EVIDENCE SCOPE',
        `request:            ${lastStateRequest?.url || '(none)'}`,
        `include_desc:       ${summary.include_descendants === true ? 'YES' : 'NO'}`,
        `scope:              ${summary.scope || selected || '(none)'}`,
        `API status:         ${lastStateRequest?.ok ? 'OK' : lastStateRequest ? 'FAILED' : 'NOT RUN'}`,
        `state count:        ${stateCount}`,
        `observation_count:  ${observationCount}`,
        `raw scoped:         ${scoped.length}`,
        `direct:              ${direct.length}`,
        `descendants:        ${descendants.length}`,
        `availability:       ${apiState.availability ?? (scoped.length ? 'observed' : 'insufficient_evidence')}`,
        `confidence:         ${apiState.confidence?.value ?? '—'}`,
        `evidence count:     ${evidenceCount}`,
        `with evidence:      ${scopedWithEvidence.length}`,
        `without evidence:   ${scopedWithoutEvidence.length}`,
        `validated records:  ${validatedCount}`,
        `evidence ids:       ${(apiState.evidence_ids || []).join(' | ') || '(none)'}`,
        '', 'OBSERVATION / EVIDENCE SEPARATION',
        `observations:        ${scoped.length}`,
        `linked evidence:    ${scopedWithEvidence.length}`,
        `unlinked:            ${scopedWithoutEvidence.length}`,
        `biological data:     ${scoped.length ? 'PRESENT' : 'ABSENT'}`,
        `evidence:            ${evidenceCount ? 'PRESENT' : 'ABSENT'}`,
        `validated state:     ${validatedCount ? 'PRESENT' : 'NOT ESTABLISHED'}`,
        '', 'STATE / OBSERVATION SEMANTICS',
        `observations exist:  ${scoped.length > 0 ? 'YES' : 'NO'}`,
        `evidence exists:     ${evidenceCount > 0 ? 'YES' : 'NO'}`,
        `state established:   ${validatedCount > 0 ? 'YES' : 'NO'}`,
        `interpretation UI:   ${interpretationUiCount ?? '(not rendered)'} element(s)`,
        `expected UI count:   ${observationCount}`,
        `interpretation check: ${interpretationUiCount === null ? 'UNKNOWN' : interpretationUiCount === observationCount ? 'PASS' : 'FAIL'}`,
        '', 'SAME-LAYER RESOLUTION',
        'Inspector layer count vs selected scope:',
        layerLines,
        '', 'Records by same-layer spatial node:',
        distributionLines,
        '', 'Same-layer duplicates on one spatial node:',
        sameLocationDuplicates.join('\n') || '(none)',
        '', 'Same biological level across multiple nodes:',
        sameLayerAcrossNodes.map(x => `  ${x}`).join('\n') || '(none)',
        '', 'Inspector/scoped mismatches:',
        inspectorMismatches.map(x => `  ${x}`).join('\n') || '(none)',
        '', 'Inspector-only layer counts:',
        inspectorOnlyLayers.map(x => `  ${x}`).join('\n') || '(none)',
        '', 'RAW OBSERVATION RESOLUTION',
        rawObservationLines,
        '', 'NAVIGATION → OBSERVATION RELATION',
        `immediate child observations: ${childObservations.length}`,
        `child subtree observations:   ${childSubtreeObservations.length}`,
        '', 'INSPECTOR SOURCE TRACE',
        LEVELS.map(level => {
          const diagnostic = layerDiagnostics.find(x => x.layer === level);
          const contributing = scoped.filter(o => o.levelKey === level)
            .map(o => `${o.id}@${o.spatial || '(none)'}`).join(', ') || '(none)';
          return `${level.toUpperCase()}\n  displayed: ${inspectorCounts[level]}\n  resolver scoped: ${diagnostic.scoped}\n  direct: ${diagnostic.direct}\n  descendants: ${diagnostic.descendants}\n  contributing: ${contributing}`;
        }).join('\n'),
        '', 'MODULE AGREEMENT',
        moduleScopeLines,
        `spatial scope:      ${allModulesAgree ? 'PASS' : 'FAIL'}`,
        `observation scope:  ${observationCount === scoped.length ? 'PASS' : 'FAIL'}`,
        `evidence separation: ${evidenceCount === scopedWithEvidence.length ? 'PASS' : 'FAIL'}`,
        `interpretation count: ${interpretationUiCount === null ? 'UNKNOWN' : interpretationUiCount === observationCount ? 'PASS' : 'FAIL'}`,
        '', 'DIAGNOSTIC HINT',
        hint
      ].join('\n');

      errors.textContent = [
        '', 'ERROR / INTERACTION',
        `last error:   ${lastError || '(none)'}`,
        `last input:   ${lastInteraction ? JSON.stringify(lastInteraction) : '(none)'}`,
        `last request: ${lastStateRequest ? JSON.stringify(lastStateRequest, null, 2) : '(none)'}`,
        '', 'LAST NAVIGATION',
        lastNavigation ? JSON.stringify(lastNavigation, null, 2) : '(none)',
        '', 'SEMANTIC CHECKS',
        semanticIssues.length ? semanticIssues.map(issue => `  FAIL · ${issue}`).join('\n') : '  PASS · no semantic mismatch detected',
        '', 'RAW DATA COUNTS',
        `all observations fetched: ${observations.length}`,
        `selected subtree:         ${scoped.length}`,
        `direct:                    ${direct.length}`,
        `descendants:              ${descendants.length}`,
        `ancestors:                ${ancestorObservations.length}`,
        `siblings:                 ${siblings.length}`
      ].join('\n');
    };

    const setMinimized = value => {
      minimized = value;
      panel.style.display = minimized ? 'none' : 'block';
      toggle.textContent = minimized ? 'DEBUG' : 'DEBUG · OPEN';
      if (!minimized) {
        fetchDiagnostics({ spatial_id: readState().selectedSpatialId || window.spatialEvidenceTarget || 'hand' });
        render();
      }
    };

    toggle.addEventListener('click', () => setMinimized(!minimized));
    document.getElementById('twin-debug-close')?.addEventListener('click', () => setMinimized(true));

    const onSpatialChange = event => {
      lastInteraction = { type: event?.type || 'spatial-change', detail: event?.detail || null };
      window.setTimeout(() => fetchDiagnostics(event?.detail || readState()), 0);
    };
    window.addEventListener('testhp:spatial-layer-changed', onSpatialChange);
    window.addEventListener('testhp:spatial-change', onSpatialChange);
    window.addEventListener('testhp:observation-updated', () => fetchDiagnostics(readState()));
    window.addEventListener('testhp:biological-state-refresh', () => fetchDiagnostics(readState()));
    window.addEventListener('testhp:navigation', event => {
      lastNavigation = event?.detail || null;
      render();
    });
    window.addEventListener('error', event => {
      lastError = event?.error?.message || event?.message || String(event);
      render();
    });
    window.addEventListener('unhandledrejection', event => {
      lastError = event?.reason?.message || String(event?.reason || event);
      render();
    });

    window.spatialViewportDebug = {
      refresh: () => fetchDiagnostics(readState()),
      render,
      readState,
      getDiagnostics: () => ({
        state: lastStatePayload,
        observations: lastObservationsPayload,
        request: lastStateRequest,
        navigation: lastNavigation,
        interaction: lastInteraction,
        error: lastError
      })
    };

    toggle.textContent = 'DEBUG';
    fetchDiagnostics(readState());
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => fetchDiagnostics(readState()), { once: true });
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
