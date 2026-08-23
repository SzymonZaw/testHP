(() => {
  const bootState = {
    startedAt: performance.now(),
    currentStep: null,
    completedSteps: [],
    lastProgress: null,
    failure: null,
    recentProgress: []
  };

  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  }[c]));

  const pushProgress = (step, detail = '') => {
    bootState.currentStep = step;
    bootState.lastProgress = { step, detail, at: performance.now() };
    bootState.recentProgress.push({ step, detail });
    if (bootState.recentProgress.length > 12) bootState.recentProgress.shift();
    window.dispatchEvent(new CustomEvent('testhp:twin-progress', { detail: { step, detail } }));
  };

  const log = (step, detail = '') => {
    const line = document.createElement('div');
    line.className = 'twin-boot-line';
    line.dataset.stepId = step;
    const labels = {
      'DOM':'DOM','Three.js + canonical viewport':'Three.js + kanoniczny widok','Spatial bridge':'Most przestrzenny','Deep 3D sync':'Synchronizacja głębokiego 3D','Evidence renderer':'Renderer danych','Viewport debug':'Diagnostyka widoku','Evidence registry':'Rejestr danych','Spatial stages 2–4':'Etapy przestrzenne 2–4','Stages 5–8':'Etapy 5–8','Evidence UX':'Obsługa danych','Viewport boot verifier':'Weryfikator uruchomienia widoku','Hand surface stages 11–15':'Etapy powierzchni dłoni 11–15','Hand surface edit bridge':'Most edycji powierzchni dłoni','Hand surface stages 20–22':'Etapy powierzchni dłoni 20–22','Photo reconstruction':'Rekonstrukcja ze zdjęć'
    };
    const visibleStep = labels[step] || step;
    line.innerHTML = `<span class="twin-boot-mark">…</span><strong>${escapeHtml(visibleStep)}</strong><span>${escapeHtml(detail)}</span>`;
    document.getElementById('twin-boot-lines')?.appendChild(line);
    pushProgress(step, detail);
  };

  const mark = (step, ok = true, detail = '') => {
    const row = document.querySelector(`#twin-boot-lines .twin-boot-line[data-step-id="${CSS.escape(step)}"]`);
    if (!row) return;
    row.querySelector('.twin-boot-mark').textContent = ok ? '✓' : '✕';
    row.classList.toggle('ok', ok);
    row.classList.toggle('error', !ok);
    if (detail) row.querySelector('span:last-child').textContent = detail;
    if (ok && !bootState.completedSteps.includes(step)) bootState.completedSteps.push(step);
  };

  const withTimeout = (promise, ms, label) => Promise.race([promise,new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} timed out after ${ms / 1000}s`)), ms))]);

  function ensureLegacyMacroPreviewCompatibility() {
    const existing = document.getElementById('macro-preview');
    if (existing) { existing.hidden = true; existing.style.setProperty('display', 'none', 'important'); return; }
    const row = document.querySelector('.macro-row'); if (!row) return;
    const preview = document.createElement('div'); preview.id = 'macro-preview'; preview.className = 'evidence-preview'; preview.hidden = true; preview.style.setProperty('display', 'none', 'important');
    preview.innerHTML = '<img id="macro-image" alt=""><div class="preview-caption"><span id="macro-filename"></span><span id="macro-view"></span></div>'; row.appendChild(preview);
  }

  function collectBootDiagnostics(error = bootState.failure) {
    const viewport = document.getElementById('twin-viewport'); const canvas = document.getElementById('twin-canvas'); const loading = document.getElementById('viewer-loading'); const manager = window.spatialViewportManager;
    const node = document.getElementById('spatial-node'); const breadcrumb = [...document.querySelectorAll('#spatial-breadcrumb button')].map(el => el.textContent.trim()).filter(Boolean);
    const children = [...document.querySelectorAll('#spatial-children .spatial-target')].map(el => ({label:el.querySelector('strong')?.textContent?.trim() || '(brak etykiety)',id:el.dataset?.spatialId || el.getAttribute('data-spatial-id') || null,disabled:!!el.disabled,connected:el.isConnected}));
    const rect = canvas?.getBoundingClientRect?.(); let webgl = 'nie sprawdzono';
    if (canvas) { try { const gl = canvas.getContext('webgl2') || canvas.getContext('webgl'); webgl = gl ? `${gl.constructor?.name || 'WebGL'} OK` : 'BRAK kontekstu WebGL/WebGL2'; } catch (webglError) { webgl = `BŁĄD getContext(): ${webglError.message}`; } }
    const scripts = [...document.scripts].map(script => script.src).filter(Boolean).filter(src => src.includes('/digital-twin/'));
    const diagnostics = {failure:error ? {name:error.name || 'Error',message:error.message || String(error),stack:error.stack || 'brak stack trace'} : null,boot:{currentStep:bootState.currentStep,completedSteps:bootState.completedSteps,initAgeMs:Math.round(performance.now()-bootState.startedAt),lastProgress:bootState.lastProgress,recentProgress:bootState.recentProgress},dom:{twinViewport:!!viewport,twinCanvas:!!canvas,viewerLoading:!!loading,debugHost:!!document.getElementById('twin-viewport-debug-host'),spatialNode:!!node,spatialChildren:!!document.getElementById('spatial-children')},canvas:canvas ? {width:canvas.width,height:canvas.height,clientWidth:canvas.clientWidth,clientHeight:canvas.clientHeight,rect:rect ? {width:Math.round(rect.width),height:Math.round(rect.height),left:Math.round(rect.left),top:Math.round(rect.top)} : null,display:getComputedStyle(canvas).display,visibility:getComputedStyle(canvas).visibility,opacity:getComputedStyle(canvas).opacity,pointerEvents:getComputedStyle(canvas).pointerEvents,webgl} : {webgl},spatial:{level:document.getElementById('spatial-level-badge')?.textContent?.trim() || '?',target:node?.querySelector('strong')?.textContent?.trim() || '?',path:breadcrumb,evidenceTarget:window.spatialEvidenceTarget || null,selectedSpatialNode:window.selectedSpatialNode || null,children},renderer:{managerPresent:!!manager,managerVersion:manager?.version || null,activeKey:manager?.activeKey || null,activeLayer:manager?.activeLayer || manager?.active?.activeLayer || null,activeType:manager?.active?.constructor?.name || null,scene:!!manager?.active?.scene,camera:!!manager?.active?.camera,deepRenderer:!!manager?.deepRenderer,setSpatialTarget:typeof manager?.setSpatialTarget === 'function',render:typeof manager?.render === 'function',canonical:!!(manager && manager.version === 'canonical-three-1' && manager.active?.scene && manager.active?.camera && manager.deepRenderer)},environment:{readyFlag:!!window.__testhpTwinReady,bootComplete:!!window.__testhpTwinBootComplete,three:typeof window.THREE !== 'undefined' ? 'global THREE present' : 'global THREE not exposed',url:location.href,userAgent:navigator.userAgent,loadedDigitalTwinScripts:scripts}};
    window.__testhpTwinBootDiagnostics = diagnostics; return diagnostics;
  }

  function renderBootDiagnostics(error) {
    const box = document.getElementById('twin-boot-diagnostics'); if (!box) return;
    const diagnostics = collectBootDiagnostics(error); const existing = document.getElementById('twin-boot-failure-details'); if (existing) existing.remove();
    const panel = document.createElement('div'); panel.id='twin-boot-failure-details'; panel.innerHTML=`<div class="twin-boot-failure-title">SZCZEGÓŁY AWARII</div><pre>${escapeHtml(JSON.stringify(diagnostics,null,2))}</pre>`; box.appendChild(panel);
  }

  function showBootUi() {
    if (document.getElementById('twin-boot-diagnostics')) return;
    const style = document.createElement('style'); style.id='twin-boot-diagnostics-css'; style.textContent=`
      #twin-debug-panel{position:fixed;right:16px;bottom:16px;z-index:2147483647;width:min(720px,calc(100vw - 32px));max-height:min(78vh,760px);overflow:auto;padding:12px;border:1px solid rgba(130,145,165,.45);border-radius:12px;background:rgba(13,17,23,.97);color:#e6edf3;font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;box-shadow:0 12px 40px rgba(0,0,0,.3)}
      #twin-debug-panel .twin-debug-header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;font:700 12px/1.2 system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase}
      #twin-debug-panel .twin-debug-toggle{border:1px solid rgba(130,145,165,.45);border-radius:6px;background:rgba(255,255,255,.06);color:#d8dee4;padding:4px 8px;cursor:pointer;font:600 10px/1 system-ui,sans-serif}
      #twin-debug-panel.twin-debug-minimized{width:auto;max-height:none;padding:0;border:0;background:transparent;box-shadow:none;overflow:visible}
      #twin-debug-panel.twin-debug-minimized > *:not(.twin-debug-header){display:none!important}
      #twin-debug-panel .twin-debug-section{margin-top:8px;padding-top:8px;border-top:1px solid rgba(130,145,165,.2)}
      .twin-boot-line{display:grid;grid-template-columns:18px 190px 1fr;gap:6px;align-items:start;padding:3px 0;color:#9da7b3}.twin-boot-line strong{color:#d8dee4}.twin-boot-line.ok .twin-boot-mark{color:#56d364}.twin-boot-line.ok strong{color:#e6edf3}.twin-boot-line.error .twin-boot-mark,.twin-boot-line.error strong{color:#ff7b72}
      .twin-boot-summary{margin-top:8px;color:#8b949e}.twin-boot-failure-title{margin-top:12px;padding-top:10px;border-top:1px solid rgba(130,145,165,.25);font:700 11px/1.2 system-ui,sans-serif;letter-spacing:.08em;color:#ff7b72}
      #twin-boot-failure-details pre{margin:8px 0 0;padding:10px;max-height:420px;overflow:auto;white-space:pre-wrap;word-break:break-word;border-radius:8px;background:rgba(0,0,0,.25);color:#c9d1d9;font:11px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
      #twin-boot-diagnostics .twin-boot-toggle{border:1px solid rgba(130,145,165,.45);border-radius:6px;background:rgba(255,255,255,.06);color:#d8dee4;padding:4px 8px;cursor:pointer;font:600 10px/1 system-ui,sans-serif}
    `; document.head.appendChild(style);

    const host = document.getElementById('twin-viewport-debug-host') || document.body;
    let panel = document.getElementById('twin-debug-panel');
    if (!panel) { panel=document.createElement('section'); panel.id='twin-debug-panel'; host.appendChild(panel); }
    panel.innerHTML='<div class="twin-debug-header"><span>TWIN VIEWPORT · DEBUG</span><button type="button" class="twin-debug-toggle">MINIMIZUJ</button></div>';
    const box=document.createElement('div'); box.id='twin-boot-diagnostics'; box.className='twin-debug-section'; box.innerHTML='<div style="display:flex;align-items:center;justify-content:space-between;gap:8px"><strong>BOOT / RUNTIME</strong><button type="button" class="twin-boot-toggle" aria-expanded="true">UKRYJ</button></div><div id="twin-boot-lines"></div><div class="twin-boot-summary">Ciężkie moduły są ładowane dopiero po przygotowaniu kanonicznego widoku.</div>';
    panel.appendChild(box);
    panel.querySelector('.twin-debug-toggle').addEventListener('click',()=>{const minimized=panel.classList.toggle('twin-debug-minimized'); panel.querySelector('.twin-debug-toggle').textContent=minimized?'ROZWIŃ':'MINIMIZUJ';});
    box.querySelector('.twin-boot-toggle').addEventListener('click',()=>{const hidden=box.classList.toggle('twin-boot-hidden'); box.querySelector('#twin-boot-lines').hidden=hidden; box.querySelector('.twin-boot-summary').hidden=hidden; box.querySelector('.twin-boot-toggle').textContent=hidden?'POKAŻ':'UKRYJ';});
  }

  async function loadClassic(src,label,timeout=10000){log(label,`ładowanie: ${src}`);await withTimeout(new Promise((resolve,reject)=>{const script=document.createElement('script');script.src=src;script.onload=resolve;script.onerror=()=>reject(new Error(`Nie udało się załadować modułu: ${src}`));document.body.appendChild(script);}),timeout,label);mark(label,true,'załadowano');}
  function loadStages58NonBlocking(){log('Stages 5–8','ładowanie w tle');const script=document.createElement('script');script.src='/digital-twin/assets/stages-5-8.js?v=stage-5-8-4';script.onload=()=>mark('Stages 5–8',true,'załadowano w tle');script.onerror=()=>mark('Stages 5–8',false,'opcjonalna warstwa niedostępna; widok działa dalej');document.body.appendChild(script);}
  window.addEventListener('error',event=>{if(event?.message)pushProgress('WINDOW ERROR',`${event.message} | ${event.filename || ''}:${event.lineno || ''}:${event.colno || ''}`);});
  window.addEventListener('unhandledrejection',event=>{pushProgress('UNHANDLED PROMISE',String(event.reason?.stack || event.reason || 'unknown'));});
  async function boot(){showBootUi();try {
