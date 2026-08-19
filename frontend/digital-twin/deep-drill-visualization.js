(() => {
  const viewport = document.getElementById('twin-viewport');
  const badge = document.getElementById('spatial-level-badge');
  const node = document.getElementById('spatial-node');
  const children = document.getElementById('spatial-children');
  if (!viewport || !badge || !node || !children) return;

  const panel = document.createElement('section');
  panel.id = 'deep-drill-visualization';
  panel.setAttribute('aria-label', 'Deep drill visualization');
  Object.assign(panel.style, {
    position: 'absolute', inset: '0', zIndex: '28', display: 'none',
    pointerEvents: 'none', overflow: 'hidden', color: '#dcece6',
    fontFamily: 'system-ui,-apple-system,Segoe UI,sans-serif'
  });
  viewport.appendChild(panel);

  const style = document.createElement('style');
  style.textContent = `
    #deep-drill-visualization .ddv-shell{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 42%,rgba(25,59,52,.72),rgba(7,15,17,.96) 72%)}
    #deep-drill-visualization .ddv-label{position:absolute;left:18px;top:18px;padding:6px 9px;border:1px solid rgba(155,216,196,.28);border-radius:8px;background:rgba(5,12,13,.78);font-size:9px;font-weight:800;letter-spacing:.12em;color:#9bd8c4}
    #deep-drill-visualization .ddv-title{position:absolute;left:18px;top:50px;font-size:15px;font-weight:800}
    #deep-drill-visualization .ddv-note{position:absolute;left:18px;bottom:18px;max-width:430px;font-size:10px;line-height:1.45;color:#9fb7b0}
    #deep-drill-visualization .tissue-slab{width:62%;height:52%;border:1px solid rgba(155,216,196,.45);border-radius:18px;transform:perspective(800px) rotateX(12deg) rotateY(-12deg);background:repeating-linear-gradient(18deg,rgba(115,177,156,.18) 0 8px,rgba(25,58,51,.28) 8px 16px),radial-gradient(circle at 30% 30%,rgba(155,216,196,.25),rgba(10,27,24,.8) 70%);box-shadow:0 28px 70px rgba(0,0,0,.5),inset 0 0 50px rgba(155,216,196,.08)}
    #deep-drill-visualization .field-grid{width:64%;height:56%;display:grid;grid-template-columns:repeat(5,1fr);grid-template-rows:repeat(4,1fr);gap:10px;padding:16px;border:1px solid rgba(155,216,196,.28);border-radius:18px;background:rgba(8,20,19,.72);box-shadow:0 25px 65px rgba(0,0,0,.48)}
    #deep-drill-visualization .field-grid span{border:1px solid rgba(155,216,196,.2);border-radius:9px;background:radial-gradient(circle at 45% 40%,rgba(155,216,196,.22),rgba(20,48,42,.35));position:relative}
    #deep-drill-visualization .field-grid span::after{content:'';position:absolute;width:14px;height:14px;left:50%;top:50%;transform:translate(-50%,-50%);border-radius:50%;border:1px solid rgba(155,216,196,.35);background:rgba(91,164,140,.16)}
    #deep-drill-visualization .cell-model{width:220px;height:220px;border-radius:50%;position:relative;border:2px solid rgba(155,216,196,.55);background:radial-gradient(circle at 32% 28%,#b8e4d4 0,#69ad99 30%,#315f53 68%,#102821 100%);box-shadow:0 0 70px rgba(95,174,152,.2),inset -25px -25px 45px rgba(0,0,0,.25)}
    #deep-drill-visualization .cell-model::before{content:'';position:absolute;width:70px;height:70px;left:50%;top:50%;transform:translate(-50%,-50%);border-radius:50%;border:2px solid rgba(155,216,196,.5);background:radial-gradient(circle at 35% 30%,#6da993,#234c40 70%);box-shadow:0 0 24px rgba(155,216,196,.12)}
    #deep-drill-visualization .cell-model::after{content:'';position:absolute;width:8px;height:8px;left:48%;top:45%;border-radius:50%;background:#dcece6;opacity:.55}
  `;
  document.head.appendChild(style);

  const level = () => {
    const value = badge.textContent.trim().toUpperCase();
    if (value.includes('SINGLE')) return 'cell';
    if (value.includes('CELLULAR')) return 'cellular';
    if (value.includes('TISSUE')) return 'tissue';
    return 'macro';
  };
  const target = () => node.querySelector('strong')?.textContent?.trim() || 'Spatial target';
  const childCount = () => children.querySelectorAll('.spatial-target').length;

  function render() {
    const current = level();
    panel.replaceChildren();
    if (current === 'macro') { panel.style.display = 'none'; return; }
    panel.style.display = 'block';

    const shell = document.createElement('div'); shell.className = 'ddv-shell';
    const label = document.createElement('div'); label.className = 'ddv-label';
    label.textContent = `DEEP DRILL · ${current.toUpperCase()}`;
    const title = document.createElement('div'); title.className = 'ddv-title'; title.textContent = target();
    const note = document.createElement('div'); note.className = 'ddv-note';
    note.textContent = `${current === 'tissue' ? 'Tissue-level navigation visualization.' : current === 'cellular' ? 'Cellular-field navigation visualization.' : 'Single-cell navigation visualization.'} This is a spatial navigation model, not biological evidence. Linked evidence is rendered separately when available.`;
    shell.append(label, title);

    if (current === 'tissue') {
      const slab = document.createElement('div'); slab.className = 'tissue-slab'; shell.appendChild(slab);
    } else if (current === 'cellular') {
      const grid = document.createElement('div'); grid.className = 'field-grid';
      for (let i = 0; i < 20; i++) grid.appendChild(document.createElement('span'));
      shell.appendChild(grid);
    } else {
      const cell = document.createElement('div'); cell.className = 'cell-model'; shell.appendChild(cell);
    }
    shell.appendChild(note);
    panel.appendChild(shell);
  }

  const observer = new MutationObserver(render);
  [badge, node, children].forEach(el => observer.observe(el, { childList: true, subtree: true, characterData: true }));
  window.addEventListener('resize', render, { passive: true });
  render();
})();