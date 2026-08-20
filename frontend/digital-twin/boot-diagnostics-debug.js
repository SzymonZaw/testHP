(() => {
  const start = () => {
    const panel = document.getElementById('twin-debug-panel');
    if (!panel) return false;

    let output = document.getElementById('twin-debug-boot-diagnostics');
    if (!output) {
      output = document.createElement('pre');
      output.id = 'twin-debug-boot-diagnostics';
      output.style.cssText = 'margin:10px 0 0;padding:10px;border:1px solid #7a5b32;border-radius:8px;background:#17110a;color:#f2d7a0;white-space:pre-wrap;font:11px/1.35 ui-monospace,SFMono-Regular,Consolas,monospace;';
      panel.appendChild(output);
    }

    const lines = [];
    const now = () => new Date().toLocaleTimeString();
    const push = message => {
      lines.push(`[${now()}] ${message}`);
      while (lines.length > 80) lines.shift();
      output.textContent = ['BOOT DIAGNOSTICS · MINIMIZATION', ...lines].join('\n');
    };

    const inspect = reason => {
      const box = document.getElementById('twin-boot-diagnostics');
      if (!box) { push(`${reason} | box=MISSING`); return; }
      const heading = box.querySelector('.twin-boot-heading');
      const title = heading?.querySelector('h3');
      const toggle = box.querySelector('.twin-boot-toggle');
      const bootLines = document.getElementById('twin-boot-lines');
      const summary = box.querySelector('.twin-boot-summary');
      const css = el => el ? getComputedStyle(el) : null;
      const state = el => {
        const s = css(el);
        if (!el || !s) return 'MISSING';
        return `display=${s.display} visibility=${s.visibility} opacity=${s.opacity} size=${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`;
      };
      const className = box.className || '(none)';
      push(`${reason}\nclass: ${className}\naria-expanded: ${toggle?.getAttribute('aria-expanded') ?? 'MISSING'}\ntoggle text: ${toggle?.textContent?.trim() ?? 'MISSING'}\nheading: ${state(heading)}\ntitle: ${state(title)}\nlines: ${state(bootLines)}\nsummary: ${state(summary)}\nbox: ${state(box)}\nbox text length: ${box.textContent?.trim().length ?? 0}\nresult: ${box.classList.contains('twin-boot-minimized') ? 'MINIMIZED CLASS PRESENT' : 'MINIMIZED CLASS ABSENT'}`);
    };

    const attach = () => {
      const box = document.getElementById('twin-boot-diagnostics');
      if (!box) return false;
      const toggle = box.querySelector('.twin-boot-toggle');
      if (toggle && !toggle.dataset.bootDebugAttached) {
        toggle.dataset.bootDebugAttached = '1';
        toggle.addEventListener('click', () => {
          push('TOGGLE CLICK captured');
          setTimeout(() => inspect('AFTER TOGGLE'), 0);
          setTimeout(() => inspect('AFTER TOGGLE +100ms'), 100);
        }, true);
      }
      if (!box.dataset.bootDebugObserved) {
        box.dataset.bootDebugObserved = '1';
        const observer = new MutationObserver(mutations => {
          const changes = mutations.map(m => `${m.type}:${m.attributeName || 'children'}`).join(',');
          push(`DOM MUTATION | ${changes}`);
          inspect('AFTER DOM MUTATION');
        });
        observer.observe(box, { attributes:true, attributeFilter:['class','style','hidden','aria-expanded'], childList:true, subtree:true });
      }
      inspect('INITIAL');
      return true;
    };

    if (attach()) return true;
    const timer = setInterval(() => { if (attach()) clearInterval(timer); }, 250);
    setTimeout(() => clearInterval(timer), 20000);
    return true;
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once:true });
  else start();
})();
