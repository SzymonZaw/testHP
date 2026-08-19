(() => {
  const panel=document.createElement('section');
  panel.className='panel';
  panel.id='stages-5-8-panel';
  panel.innerHTML=`<div class="panel-title"><div><span class="section-kicker">SILNIK CYFROWEGO BLIŹNIAKA</span><strong>ETAPY 5–8</strong></div><span class="research-badge">TYLKO DO BADAŃ</span></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:16px"><article class="state-card"><span>Warstwa danych</span><strong id="s58-evidence">Warstwa danych</strong><small>Etap 5 · dane przypisane przestrzennie</small></article><article class="state-card"><span>Anatomia</span><strong id="s58-anatomy">Struktura anatomiczna</strong><small>Etap 6 · kontekst głębokości</small></article><article class="state-card"><span>Postępująca rozdzielczość</span><strong id="s58-resolution">Postępująca rozdzielczość biologiczna</strong><small>Etap 7 · zachowany kontekst</small></article><article class="state-card"><span>Historia podłużna</span><strong id="s58-longitudinal">Bliźniak w czasie</strong><small>Etap 8 · bliźniak uwzględniający czas</small></article></div><div id="s58-findings" style="padding:0 16px 16px"></div>`;

  const mount=()=>{
    const anchor=document.querySelector('.timeline');
    if(anchor && !document.getElementById('stages-5-8-panel')) anchor.after(panel);
    const findings=document.getElementById('s58-findings');
    if(findings) findings.textContent='Etapy 5–8 są zarejestrowane. Dane są jawnymi danymi badawczymi; cele nawigacyjne nie oznaczają istnienia ustaleń biologicznych.';
  };

  // Etapy 5–8 nie blokują głównej ścieżki uruchomienia widoku.
  // Silnik powierzchni dłoni pozostaje niezależnym modułem.
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
