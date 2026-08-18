const SCALE_ORDER = ['macro', 'tissue', 'cellular', 'cell'];
const SCALE_LABELS = {
  macro: 'Macro anatomy',
  tissue: 'Tissue field',
  cellular: 'Cellular field',
  cell: 'Single cell'
};

const breadcrumb = document.getElementById('spatial-breadcrumb');
const navigator = document.querySelector('.spatial-navigator');
if (!breadcrumb || !navigator) return;

const switcher = document.createElement('div');
switcher.id = 'spatial-layer-switcher';
switcher.setAttribute('aria-label', 'Visualization layer selector');
switcher.innerHTML = `<span class="spatial-layer-switcher-label">VISUALIZATION LAYER</span>`;
navigator.insertBefore(switcher, breadcrumb);

function levelIndex(level) {
  return SCALE_ORDER.indexOf(level);
}

function currentLevel() {
  const badge = document.getElementById('spatial-level-badge');
  const text = String(badge?.textContent || '').toUpperCase();
  if (text.includes('SINGLE')) return 'cell';
  if (text.includes('CELLULAR')) return 'cellular';
  if (text.includes('TISSUE')) return 'tissue';
  return 'macro';
}

function render() {
  const buttons = [...breadcrumb.querySelectorAll('button')];
  const current = currentLevel();
  const currentIndex = levelIndex(current);
  switcher.replaceChildren();

  const label = document.createElement('span');
  label.className = 'spatial-layer-switcher-label';
  label.textContent = 'VISUALIZATION LAYER';
  switcher.appendChild(label);

  SCALE_ORDER.forEach(level => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'spatial-layer-choice';
    button.textContent = SCALE_LABELS[level];
    button.title = `Show ${SCALE_LABELS[level]} visualization`;

    const targetIndex = levelIndex(level);
    const available = targetIndex <= currentIndex && buttons.length > targetIndex;
    button.disabled = !available;
    if (level === current) button.classList.add('active');

    if (available) {
      // Breadcrumb layout is one node per spatial level; the first macro node
      // is the hand root and the second macro node is the selected region.
      // Prefer the selected macro region when returning to Macro.
      let buttonIndex = targetIndex;
      if (level === 'macro' && buttons.length > 1) buttonIndex = 1;
      const target = buttons[buttonIndex];
      if (target) button.onclick = () => target.click();
    }
    switcher.appendChild(button);
  });
}

new MutationObserver(render).observe(breadcrumb, { childList: true, subtree: true, characterData: true });
const badge = document.getElementById('spatial-level-badge');
if (badge) new MutationObserver(render).observe(badge, { childList: true, subtree: true, characterData: true });
render();
