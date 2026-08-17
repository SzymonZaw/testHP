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

  const scaleNames = {
    MACRO: 'Macro anatomy',
    'TISSUE FIELD': 'Tissue section',
    'CELLULAR FIELD': 'Cellular field',
    'SINGLE CELL': 'Single cell'
  };

  function currentLevel() {
    return String(badge.textContent || 'MACRO').trim().toUpperCase();
  }

  function renderPlane() {
    const level = currentLevel();
    const deeper = level !== 'MACRO';
    plane.hidden = !deeper;
    if (canvas) canvas.style.visibility = deeper ? 'hidden' : 'visible';
    if (controls) controls.style.visibility = deeper ? 'hidden' : 'visible';
    if (hint) hint.style.visibility = deeper ? 'hidden' : 'visible';
    if (loading) loading.style.visibility = deeper ? 'hidden' : 'visible';
    if (!deeper) return;

    plane.replaceChildren();
    const header = document.createElement('div');
    header.className = 'plane-header';
    const eyebrow = document.createElement('span');
    eyebrow.textContent = scaleNames[level] || level;
    const title = document.createElement('strong');
    title.textContent = node.querySelector('strong')?.textContent || 'Selected spatial target';
    header.append(eyebrow, title);
    plane.appendChild(header);

    const field = document.createElement('div');
    field.className = `plane-field plane-${level.toLowerCase().replaceAll(' ', '-')}`;

    const targets = [...children.querySelectorAll('.spatial-target')];
    if (targets.length) {
      targets.forEach((target, index) => {
        const visual = document.createElement('button');
        visual.type = 'button';
        visual.className = 'plane-target';
        visual.dataset.index = String(index);
        const targetTitle = document.createElement('strong');
        targetTitle.textContent = target.querySelector('strong')?.textContent || `Spatial target ${index + 1}`;
        const targetScale = document.createElement('span');
        targetScale.textContent = target.querySelector('span')?.textContent || 'Navigation target';
        visual.append(targetTitle, targetScale);
        visual.addEventListener('click', () => target.click());
        field.appendChild(visual);
      });
    } else {
      const selected = document.createElement('div');
      selected.className = 'plane-cell-target';
      selected.innerHTML = '<span>SELECTED TARGET</span><strong>Single cell</strong><small>Navigation only · no linked evidence</small>';
      field.appendChild(selected);
    }
    plane.appendChild(field);

    const note = document.createElement('div');
    note.className = 'plane-note';
    note.textContent = 'Spatial visualization only. This plane does not represent tissue, microscopy, or cellular findings unless real evidence is explicitly linked to this target.';
    plane.appendChild(note);
  }

  const observer = new MutationObserver(renderPlane);
  observer.observe(badge, { childList: true, characterData: true, subtree: true });
  observer.observe(node, { childList: true, characterData: true, subtree: true });
  observer.observe(children, { childList: true, characterData: true, subtree: true });
  renderPlane();
}