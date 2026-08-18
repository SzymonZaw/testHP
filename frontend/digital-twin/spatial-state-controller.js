import { createSpatialNodeState, spatialNodeKey } from './spatial-node-state.js';

const breadcrumb = document.getElementById('spatial-breadcrumb');
const node = document.getElementById('spatial-node');
const badge = document.getElementById('spatial-level-badge');

if (breadcrumb && node && badge) {
  let analysis = null;
  let lastKey = '';

  const levelFromBadge = () => {
    const value = badge.textContent.trim().toLowerCase();
    if (value.includes('single')) return 'cell';
    if (value.includes('cellular')) return 'cellular';
    if (value.includes('tissue')) return 'tissue';
    return 'macro';
  };

  const knownRegions = new Set(['hand', 'wrist', 'palm', 'thumb', 'index finger', 'middle finger', 'ring finger', 'little finger']);
  const regionId = path => {
    const match = [...path].reverse().find(label => knownRegions.has(label.toLowerCase()));
    return match ? match.toLowerCase().replaceAll(' ', '_').replace('index_finger', 'index').replace('middle_finger', 'middle').replace('ring_finger', 'ring').replace('little_finger', 'little') : '';
  };

  const linkedEvidence = (resolution, path) => {
    const region = regionId(path);
    if (!region || !analysis?.assets) return [];
    return analysis.assets.filter(asset => {
      if (!['ready', 'available'].includes(String(asset.status || '').toLowerCase())) return false;
      const assetRegion = String(asset.region_id || asset.zone_id || '').toLowerCase();
      if (assetRegion !== region) return false;
      const modality = String(asset.modality || '').toLowerCase();
      if (resolution === 'tissue') return modality === 'wsi';
      if (resolution === 'cellular' || resolution === 'cell') return modality === 'microscopy' || modality === 'cellular';
      if (resolution === 'macro') return modality === 'hand';
      return false;
    });
  };

  const sync = () => {
    const path = [...breadcrumb.querySelectorAll('button')].map(button => button.textContent.trim()).filter(Boolean);
    const resolution = levelFromBadge();
    const target = node.querySelector('strong')?.textContent.trim() || path.at(-1) || 'Hand';
    const parent = path.length > 1 ? { target: path.at(-2), resolution: resolution === 'macro' ? 'macro' : 'macro' } : null;
    const children = [...document.querySelectorAll('#spatial-children .spatial-target strong')].map(el => ({ label: el.textContent.trim() }));
    const state = createSpatialNodeState({ resolution, target, path, parent, children, evidence: linkedEvidence(resolution, path) });
    const key = spatialNodeKey(state);
    if (key === lastKey) return;
    lastKey = key;
    window.spatialNodeState = state;
    if (window.spatialViewportManager) window.spatialViewportManager.currentSpatialNodeState = state;
    window.dispatchEvent(new CustomEvent('spatial-node-state-changed', { detail: state }));
  };

  window.addEventListener('hand-analysis-updated', event => { analysis = event.detail || analysis; sync(); });
  new MutationObserver(sync).observe(breadcrumb.parentElement, { childList: true, subtree: true, characterData: true });
  sync();
}
