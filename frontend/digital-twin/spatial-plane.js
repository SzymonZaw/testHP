const viewport = document.getElementById('twin-viewport');
const canvas = document.getElementById('twin-canvas');
const controls = document.querySelector('.viewer-controls');
const hint = document.querySelector('.viewer-hint');
const loading = document.getElementById('viewer-loading');
const badge = document.getElementById('spatial-level-badge');
const node = document.getElementById('spatial-node');
const children = document.getElementById('spatial-children');

if (viewport && badge && node && children) {
  const plane = document.createElement('div');
  plane.id = 'spatial-plane';
  plane.className = 'spatial-plane';
  plane.hidden = true;
  viewport.appendChild(plane);

  const scaleNames = { MACRO: 'Macro anatomy', 'TISSUE FIELD': 'Tissue section', 'CELLULAR FIELD': 'Cellular field', 'SINGLE CELL': 'Single cell' };

  function currentLevel() { return String(badge.textContent || 'MACRO').trim().toUpperCase(); }
  function makeTargetButton(target, className = 'plane-target') {
    const visual = document.createElement('button'); visual.type = 'button'; visual.className = className;
    const title = document.createElement('strong'); title.textContent = target.querySelector('strong')?.textContent || 'Spatial target';
    const scale = document.createElement('span'); scale.textContent = target.querySelector('span')?.textContent || 'Navigation target';
    visual.append(title, scale); visual.addEventListener('click', () => target.click()); return visual;
  }

  function renderTissue(field, targets) {
    field.classList.add('plane-tissue-visual');
    const section = document.createElement('div'); section.className = 'tissue-section-shape';
    const label = document.createElement('span'); label.textContent = 'TISSUE SPATIAL FIELD · NAVIGATION ONLY'; section.appendChild(label);
    targets.forEach((target, index) => { const region = makeTargetButton(target, 'plane-region plane-region-tissue'); region.style.setProperty('--region-index', index); section.appendChild(region); });
    field.appendChild(section);
  }

  function renderCellular(field, targets) {
    field.classList.add('plane-cellular-visual');
    const grid = document.createElement('div'); grid.className = 'cellular-field-grid';
    for (let i = 0; i < 49; i += 1) { const mark = document.createElement('i'); mark.className = 'cellular-grid-mark'; grid.appendChild(mark); }
    field.appendChild(grid);
    const label = document.createElement('span'); label.className = 'cellular-field-label'; label.textContent = 'MICROSCOPY FIELD · NAVIGATION ONLY'; field.appendChild(label);
    targets.forEach((target, index) => { const cell = makeTargetButton(target, 'plane-cell-marker'); cell.style.setProperty('--cell-index', index); field.appendChild(cell); });
  }

  function renderSingleCell(field) {
    field.classList.add('plane-single-cell-visual');
    const halo = document.createElement('div'); halo.className = 'single-cell-halo';
    const cell = document.createElement('div'); cell.className = 'single-cell-shape';
    const nucleus = document.createElement('div'); nucleus.className = 'single-cell-nucleus'; cell.appendChild(nucleus); halo.appendChild(cell); field.appendChild(halo);
    const label = document.createElement('div'); label.className = 'single-cell-label';
    label.innerHTML = '<span>SELECTED TARGET</span><strong>Single cell</strong><small>Navigation only · no linked evidence</small>'; field.appendChild(label);
  }

  function renderPlane() {
    const level = currentLevel(); const deeper = level !== 'MACRO'; plane.hidden = !deeper;
    if (canvas) canvas.style.visibility = deeper ? 'hidden' : 'visible';
    if (controls) controls.style.visibility = deeper ? 'hidden' : 'visible';
    if (hint) hint.style.visibility = deeper ? 'hidden' : 'visible';
    if (loading) loading.style.visibility = deeper ? 'hidden' : 'visible';
    if (!deeper) return;

    plane.replaceChildren();
    const header = document.createElement('div'); header.className = `plane-header plane-header-${level.toLowerCase().replaceAll(' ', '-')}`;
    const eyebrow = document.createElement('span'); eyebrow.textContent = scaleNames[level] || level;
    const title = document.createElement('strong'); title.textContent = node.querySelector('strong')?.textContent || 'Selected spatial target';
    header.append(eyebrow, title); plane.appendChild(header);

    const field = document.createElement('div'); field.className = `plane-field plane-${level.toLowerCase().replaceAll(' ', '-')}`;
    const targets = [...children.querySelectorAll('.spatial-target')];
    if (level === 'TISSUE FIELD') renderTissue(field, targets);
    else if (level === 'CELLULAR FIELD') renderCellular(field, targets);
    else renderSingleCell(field);
    plane.appendChild(field);

    const note = document.createElement('div'); note.className = 'plane-note';
    note.textContent = 'Spatial visualization only. This plane is a navigation model and does not represent tissue, microscopy, or cellular findings unless real evidence is explicitly linked to this target.';
    plane.appendChild(note);
  }

  const observer = new MutationObserver(renderPlane);
  observer.observe(badge, { childList: true, characterData: true, subtree: true });
  observer.observe(node, { childList: true, characterData: true, subtree: true });
  observer.observe(children, { childList: true, characterData: true, subtree: true });
  renderPlane();
}