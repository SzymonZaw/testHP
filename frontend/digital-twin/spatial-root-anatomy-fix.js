import('./spatial-target-canonicalizer.js?v=canonical-target-2').catch(error => console.error('[Twin navigation] target canonicalizer failed to load', error));
import('./spatial-writer-debug.js?v=writer-debug-2').catch(error => console.error('[Twin navigation] writer debug failed to load', error));

(() => {
  const ROOT_PARTS = [
    { id: 'palm', label: 'Śródręcze', level: 'macro', regionId: 'palm' },
    { id: 'thumb', label: 'Kciuk', level: 'macro', regionId: 'thumb' },
    { id: 'index', label: 'Palec wskazujący', level: 'macro', regionId: 'index' },
    { id: 'middle', label: 'Palec środkowy', level: 'macro', regionId: 'middle' },
    { id: 'ring', label: 'Palec serdeczny', level: 'macro', regionId: 'ring' },
    { id: 'little', label: 'Mały palec', level: 'macro', regionId: 'little' },
    { id: 'wrist', label: 'Nadgarstek', level: 'macro', regionId: 'wrist' }
  ];

  const $ = id => document.getElementById(id);
  const labels = () => [...document.querySelectorAll('#spatial-breadcrumb button')].map(b => b.textContent.trim()).filter(Boolean);
  const currentIsRoot = () => {
    const path = labels();
    return path.length === 1 && /^(dłoń|hand)$/i.test(path[0]);
  };

  const canonicalTarget = value => {
    if (!value) return null;
    const raw = typeof value === 'string' ? value : value.spatial_node_id || value.spatial_id || value.spatialId || value.targetSpatialId || value.target || null;
    if (!raw) return null;
    return {
      'hand/palm/hypothenar-eminence': 'hand/palm/hypothenar',
      'hand/palm/thenar-eminence': 'hand/palm/thenar',
      'hand/palm/central-palm-eminence': 'hand/palm/central-palm'
    }[raw] || raw;
  };

  // One-time migration of an already-ingested hand asset into the explicit
  // deep spatial contract. The asset is discovered from the live ingestion
  // registry rather than relying on a stale hard-coded asset id. This reuses
  // the real registered file through the canonical upload/attach endpoint;
  // no synthetic evidence or local-only registry record is created.
  const PREFERRED_ASSET_ID = 'aif6yv';
  const EXPLICIT_TARGET = 'hand/palm/hypothenar';
  let explicitAttachPromise = null;

  async function ensureHypothenarEvidence() {
    const target = canonicalTarget(
      window.spatialEvidenceTarget ||
      window.selectedSpatialNode ||
      window.spatialViewportManager?.state?.spatialTarget ||
      window.spatialViewportManager?.active?.spatial_id
    );
    if (target !== EXPLICIT_TARGET) return;
    if (explicitAttachPromise) return explicitAttachPromise;

    explicitAttachPromise = (async () => {
      try {
        const registryResponse = await fetch(`/api/spatial/registry?subject_id=own_cohort&timepoint=T0&spatial_node_id=${encodeURIComponent(EXPLICIT_TARGET)}`, { cache: 'no-store' });
        if (!registryResponse.ok) return;
        const registry = await registryResponse.json();
        if (Array.isArray(registry.items) && registry.items.length) {
          window.dispatchEvent(new CustomEvent('testhp:evidence-attached', { detail: { target: EXPLICIT_TARGET, status: 'already-attached', count: registry.items.length } }));
          return;
        }

        const assetsResponse = await fetch('/api/ingestion/assets', { cache: 'no-store' });
        if (!assetsResponse.ok) {
          window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'explicit-evidence-attach', target: EXPLICIT_TARGET, status: 'asset-registry-unavailable', httpStatus: assetsResponse.status } }));
          return;
        }
        const assetsPayload = await assetsResponse.json();
        const assets = Array.isArray(assetsPayload.assets) ? assetsPayload.assets : [];
        const availableHandAssets = assets.filter(item => item?.status === 'available' && item?.modality === 'hand' && item?.subject_id === 'own_cohort' && item?.timepoint === 'T0');
        const sourceAsset = availableHandAssets.find(item => String(item.asset_id) === PREFERRED_ASSET_ID) || availableHandAssets[0];
        if (!sourceAsset?.asset_id) {
          window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'explicit-evidence-attach', target: EXPLICIT_TARGET, status: 'source-missing', reason: 'no available hand asset for own_cohort/T0' } }));
          return;
        }

        const sourceResponse = await fetch(`/api/spatial/evidence/${encodeURIComponent(sourceAsset.asset_id)}`, { cache: 'no-store' });
        if (!sourceResponse.ok) {
          window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'explicit-evidence-attach', target: EXPLICIT_TARGET, assetId: sourceAsset.asset_id, status: 'source-missing', httpStatus: sourceResponse.status } }));
          return;
        }
        const blob = await sourceResponse.blob();
        const sourceName = sourceResponse.headers.get('X-Spatial-Source') || sourceAsset.filename || `hand-${sourceAsset.asset_id}.bin`;
        const file = new File([blob], sourceName, { type: blob.type || sourceAsset.media_type || 'application/octet-stream' });
        const form = new FormData();
        form.append('file', file);
        form.append('subject_id', 'own_cohort');
        form.append('timepoint', 'T0');
        form.append('spatial_node_id', EXPLICIT_TARGET);
        form.append('spatial_level', 'tissue');
        form.append('modality', 'hand');
        form.append('source', `explicit-spatial-attachment:${sourceAsset.asset_id}`);

        const attachResponse = await fetch('/api/spatial/attach', { method: 'POST', body: form });
        const payload = await attachResponse.json().catch(() => ({}));
        if (!attachResponse.ok) throw new Error(payload.detail || `spatial attach HTTP ${attachResponse.status}`);

        window.spatialEvidenceTarget = EXPLICIT_TARGET;
        window.dispatchEvent(new CustomEvent('testhp:evidence-attached', { detail: { target: EXPLICIT_TARGET, status: 'attached', sourceAssetId: sourceAsset.asset_id, evidence: payload.evidence || null } }));
        window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'explicit-evidence-attach', target: EXPLICIT_TARGET, assetId: sourceAsset.asset_id, status: 'attached', evidenceId: payload.evidence?.evidence_id || null, attachedAssetId: payload.evidence?.asset_id || null } }));
      } catch (error) {
        console.error('[Twin navigation] explicit hypothenar evidence attach failed', error);
        window.dispatchEvent(new CustomEvent('testhp:diagnostic', { detail: { type: 'explicit-evidence-attach', target: EXPLICIT_TARGET, status: 'error', message: error.message || String(error) } }));
      } finally {
        explicitAttachPromise = null;
      }
    })();
    return explicitAttachPromise;
  }

  function setDiagnostic(detail) {
    window.__testhpSpatialNavDiagnostic = {
      reason: detail,
      rootTarget: 'Dłoń',
      expectedChildren: ROOT_PARTS.map(x => x.label),
      expectedChildLevel: 'Anatomia makro',
      invalidFallback: 'Regional field',
      source: 'spatial-root-anatomy-fix.js'
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-diagnostic', { detail: window.__testhpSpatialNavDiagnostic }));
  }

  function activate(part) {
    const target = { ...part, spatial_id: part.id, spatialId: part.id };
    const manager = window.spatialViewportManager;
    if (manager?.setSpatialTarget) {
      try {
        manager.setSpatialTarget(target);
        if (window.testhpSpatialContract?.publish) window.testhpSpatialContract.publish(target);
        setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń.`);
        return;
      } catch (error) {
        console.error('[Twin navigation] target selection failed', error);
      }
    }
    window.dispatchEvent(new CustomEvent('testhp:spatial-target-request', { detail: target }));
    if (window.testhpSpatialContract?.publish) window.testhpSpatialContract.publish(target);
    setDiagnostic(`Selected anatomical part '${part.label}' from root Dłoń; renderer manager was unavailable.`);
  }

  function installButtonStyle(button) {
    button.disabled = false;
    button.removeAttribute('aria-disabled');
    button.style.pointerEvents = 'auto';
    button.style.cursor = 'pointer';
    button.style.position = 'relative';
    button.style.zIndex = '1';
  }

  function isCanonicalRootDom(children) {
    const direct = [...children.children];
    if (direct.length !== ROOT_PARTS.length) return false;
    if (!direct.every(el => el.matches('button.spatial-root-anatomical-part.spatial-target'))) return false;
    const directLabels = direct.map(el => el.querySelector(':scope > strong')?.textContent?.trim() || '');
    if (!directLabels.every((value, i) => value === ROOT_PARTS[i].label)) return false;
    if (children.querySelector('.spatial-root-anatomical-part .spatial-target')) return false;
    return true;
  }

  function installDelegatedRootClick() {
    if (window.__testhpRootMacroClickHandlerInstalled) return;
    window.__testhpRootMacroClickHandlerInstalled = true;
    document.addEventListener('click', event => {
      const button = event.target?.closest?.('#spatial-children > .spatial-root-anatomical-part');
      if (!button || !currentIsRoot()) return;
      const part = ROOT_PARTS.find(x => x.id === button.dataset.spatialId);
      if (!part) return;
      event.preventDefault();
      event.stopPropagation();
      activate(part);
    }, true);
  }

  function renderRootParts() {
    const children = $('spatial-children');
    if (!children || !currentIsRoot()) return false;

    if (isCanonicalRootDom(children)) {
      children.querySelectorAll(':scope > .spatial-root-anatomical-part').forEach(installButtonStyle);
      setDiagnostic('Root Dłoń has exactly 7 direct anatomical macro targets; no nested navigation targets.');
      return false;
    }

    children.replaceChildren();
    ROOT_PARTS.forEach(part => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'spatial-target spatial-root-anatomical-part';
      button.dataset.spatialId = part.id;
      button.dataset.rootAnatomicalPart = part.id;
      const title = document.createElement('strong');
      title.textContent = part.label;
      const meta = document.createElement('span');
      meta.textContent = 'Anatomia makro';
      button.append(title, meta);
      installButtonStyle(button);
      button.addEventListener('click', event => {
        event.preventDefault();
        event.stopPropagation();
        activate(part);
      });
      children.appendChild(button);
    });

    setDiagnostic("Root Dłoń was normalized: only direct anatomical macro targets remain; stale nested targets were removed.");
    return true;
  }

  function install() {
    installDelegatedRootClick();
    let scheduled = false;
    const tryApply = () => {
      scheduled = false;
      if (currentIsRoot()) renderRootParts();
      ensureHypothenarEvidence();
    };
    const schedule = () => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(tryApply);
    };

    tryApply();
    const observer = new MutationObserver(schedule);
    ['spatial-breadcrumb', 'spatial-children', 'spatial-node', 'spatial-level-badge'].forEach(id => {
      const el = $(id);
      if (el) observer.observe(el, { childList: true, subtree: true, characterData: true });
    });
    window.addEventListener('testhp:viewport-manager-ready', schedule);
    window.addEventListener('testhp:spatial-layer-changed', schedule);
    window.addEventListener('testhp:spatial-target-changed', schedule);
    window.addEventListener('testhp:viewport-rendered', schedule);
    window.addEventListener('beforeunload', () => observer.disconnect(), { once: true });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, { once: true });
  else install();
})();
