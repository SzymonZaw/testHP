import { getDigitalTwinState, subscribeDigitalTwinState } from './canonical-ui-runtime.js';

const host = () => document.getElementById('testhp-end-user-layer');
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function activeReference(state) {
  return (Array.isArray(state.assets) ? state.assets : []).some(a => String(a.ownership ?? '').toLowerCase() === 'reference' && ['ready','available','verified','usable'].includes(String(a.status ?? '').toLowerCase()));
}

function render() {
  const root = host(); if (!root) return;
  const state = getDigitalTwinState();
  if (!activeReference(state)) return;
  root.classList.add('dt-exploration-first');
  const workspace = root.querySelector('.workspace');
  if (!workspace || workspace.dataset.explorationFirst === '1') return;
  workspace.dataset.explorationFirst = '1';
  const center = workspace.querySelector('.center');
  if (center) {
    const head = center.querySelector('.viewer-head');
    if (head && !head.querySelector('.dt-explore-context')) {
      const context = document.createElement('div');
      context.className = 'dt-explore-context';
      context.innerHTML = '<strong>REFERENCE HAND</strong><span>NIH 3D · 3DPX-017237</span><em>Reference geometry · not user health data</em>';
      head.prepend(context);
    }
    const viewport = center.querySelector('.viewport');
    if (viewport && !viewport.querySelector('.dt-explore-hint')) {
      const hint = document.createElement('div');
      hint.className = 'dt-explore-hint';
      hint.innerHTML = '<b>Explore the hand</b><span>Select a region to continue · semantic region mapping remains NOT ESTABLISHED</span>';
      viewport.appendChild(hint);
    }
  }
  const right = workspace.querySelector('.right');
  if (right && !right.querySelector('.dt-next-step')) {
    const next = document.createElement('section');
    next.className = 'card dt-next-step';
    next.innerHTML = '<div class="eyebrow">NEXT STEP</div><strong>Select a hand region</strong><span>Start with Palm, then continue to tissue, cell and molecular evidence when supplied.</span>';
    right.prepend(next);
  }
}

const start = () => { render(); subscribeDigitalTwinState(render); };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once:true }); else start();
