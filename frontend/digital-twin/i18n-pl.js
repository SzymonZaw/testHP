(() => {
  const exact = new Map(Object.entries({
    'Digital Twin · boot diagnostics':'Cyfrowy bliźniak · diagnostyka uruchomienia',
    'Digital Twin ready':'Cyfrowy bliźniak gotowy',
    'Twin Viewport error':'Błąd widoku cyfrowego bliźniaka',
    'Three.js + canonical viewport':'Three.js + kanoniczny widok',
    'app.js loaded':'app.js załadowany',
    'Spatial bridge':'Most przestrzenny',
    'Evidence renderer':'Renderer danych',
    'Viewport debug':'Diagnostyka widoku',
    'Evidence registry':'Rejestr danych',
    'Spatial stages 2–4':'Etapy przestrzenne 2–4',
    'Stages 5–8':'Etapy 5–8',
    'Evidence UX':'Obsługa danych',
    'Deep drill':'Analiza pogłębiona',
    'Viewport boot verifier':'Weryfikator uruchomienia widoku',
    'Hand surface stages 11–15':'Etapy powierzchni dłoni 11–15',
    'Hand surface edit bridge':'Most edycji powierzchni dłoni',
    'Hand surface stages 20–22':'Etapy powierzchni dłoni 20–22',
    'Photo reconstruction':'Rekonstrukcja ze zdjęć',
    'Heavy modules are loaded only after the canonical viewport is ready.':'Ciężkie moduły są ładowane dopiero po przygotowaniu kanonicznego widoku.',
    'Enable photo reconstruction':'Włącz rekonstrukcję ze zdjęć',
    'Macro anatomy':'Anatomia makro', 'Tissue field':'Pole tkankowe', 'Cellular field':'Pole komórkowe', 'Single cell':'Pojedyncza komórka',
    'spatial target':'cel przestrzenny', 'Navigation only':'Tylko nawigacja', 'navigation only':'tylko nawigacja',
    'Finest spatial target':'Najbardziej szczegółowy cel przestrzenny',
    'Hand':'Dłoń', 'Palm':'Śródręcze', 'Wrist':'Nadgarstek', 'Thumb':'Kciuk',
    'Index finger':'Palec wskazujący', 'Middle finger':'Palec środkowy', 'Ring finger':'Palec serdeczny', 'Little finger':'Mały palec',
    'Thenar eminence':'Kłąb kciuka', 'Hypothenar eminence':'Kłębik dłoni', 'Central palm':'Centralna część dłoni',
    'Proximal segment':'Odcinek bliższy', 'Middle segment':'Odcinek środkowy', 'Distal segment':'Odcinek dalszy',
    'Microscopy field A':'Pole mikroskopowe A', 'Microscopy field B':'Pole mikroskopowe B', 'Microscopy field C':'Pole mikroskopowe C',
    'Cell target 1':'Cel komórkowy 1', 'Cell target 2':'Cel komórkowy 2', 'Cell target 3':'Cel komórkowy 3',
    'OBSERVED':'OBSERWOWANE', 'Observed':'Obserwowane', 'NONE':'BRAK', 'MISSING':'BRAK', 'PARENT':'NADRZĘDNE', 'REGION':'REGION', 'LINKED':'PRZYPISANE',
    'Unavailable':'Niedostępne', 'No evidence':'Brak danych', 'Not shown at this resolution':'Nieprezentowane na tym poziomie',
    'Parent evidence only':'Tylko dane z regionu nadrzędnego', 'Linked evidence':'Przypisane dane', 'No modality':'Brak modalności',
    'Not established':'Nieustalone', 'Insufficient evidence':'Niewystarczające dane',
    'No tissue / WSI evidence is explicitly linked to this region.':'Brak danych tkankowych / WSI jawnie przypisanych do tego regionu.',
    'No tissue / WSI evidence is linked to this target. The node remains navigation only.':'Brak danych tkankowych / WSI przypisanych do tego celu. Węzeł pozostaje wyłącznie nawigacyjny.',
    'Cellular evidence requires explicitly linked microscopy data.':'Dane komórkowe wymagają jawnie przypisanych danych mikroskopowych.',
    'No cellular evidence is linked to this field. The visualization is a navigation target only.':'Brak danych komórkowych przypisanych do tego pola. Wizualizacja jest wyłącznie celem nawigacyjnym.',
    'No molecular measurements are explicitly linked to this region.':'Brak pomiarów molekularnych jawnie przypisanych do tego regionu.',
    'Evidence layer':'Warstwa danych', 'Anatomy':'Anatomia', 'Anatomical structure':'Struktura anatomiczna',
    'Progressive resolution':'Postępująca rozdzielczość', 'Progressive biological resolution':'Postępująca rozdzielczość biologiczna',
    'Longitudinal':'Podłużna historia', 'Longitudinal twin':'Bliźniak w czasie', 'RESEARCH ONLY':'TYLKO DO BADAŃ',
    'Observation data':'Dane obserwacji', 'Add observation':'Dodaj obserwację', 'Add biological observation':'Dodaj obserwację biologiczną',
    'Edit':'Edytuj', 'Remove':'Usuń', 'Details':'Szczegóły', 'Archive':'Archiwizuj', 'All':'Wszystkie', 'Archived':'Zarchiwizowane',
    'Stage 11 contract':'Kontrakt etapu 11', 'one spatial target per observation':'jeden cel przestrzenny dla każdej obserwacji',
    'editable metadata and notes':'edytowalne metadane i notatki', 'archive instead of destructive loss':'archiwizacja zamiast nieodwracalnego usuwania',
    'provenance history stays with the record':'historia pochodzenia pozostaje przy rekordzie', 'Prepare image':'Przygotowanie obrazu',
    'Natural geometry':'Naturalna geometria', 'Surface mapping':'Mapowanie powierzchni', 'Workflow':'Przepływ pracy',
    'Real images → prepared surface → registration':'Prawdziwe zdjęcia → przygotowana powierzchnia → rejestracja',
    'Stage 12 · Image preparation':'Etap 12 · przygotowanie obrazu', 'Stage 13 · Natural hand geometry':'Etap 13 · naturalna geometria dłoni',
    'Stage 14 · Surface mapping':'Etap 14 · mapowanie powierzchni', 'Stage 15 · Workflow':'Etap 15 · przepływ pracy',
    'Stage 20 · Registration QA':'Etap 20 · kontrola jakości rejestracji', 'Stage 21 · Projection plan':'Etap 21 · plan projekcji', 'Stage 22 · Twin package':'Etap 22 · pakiet bliźniaka',
    'HAND SURFACE PIPELINE':'POTOK POWIERZCHNI DŁONI', 'registration → projection plan → exportable twin package':'rejestracja → plan projekcji → pakiet bliźniaka do eksportu',
    'Registration QA':'Kontrola jakości rejestracji', 'Projection plan':'Plan projekcji', 'Twin package':'Pakiet bliźniaka',
    'Registration contract':'Kontrakt rejestracji', 'Registration quality':'Jakość rejestracji', 'Coordinate system:':'Układ współrzędnych:',
    'quality is explicit and editable':'jakość jest jawna i edytowalna', 'missing views remain missing; no synthetic evidence is invented':'brakujące widoki pozostają brakujące; nie tworzymy sztucznych danych',
    'Current spatial target':'Bieżący cel przestrzenny', 'Prepared assets in registry':'Przygotowane zasoby w rejestrze', 'Recheck':'Sprawdź ponownie', 'Open Stage 14':'Otwórz etap 14',
    'Rebuild plan':'Przebuduj plan', 'Save plan':'Zapisz plan', 'Projection rules':'Zasady projekcji', 'Export package JSON':'Eksportuj pakiet JSON', 'Refresh validation':'Odśwież walidację',
    'READY FOR TESTING':'GOTOWE DO TESTÓW', 'REVIEW REQUIRED':'WYMAGA WERYFIKACJI', 'Evidence management':'Zarządzanie danymi', 'Observations':'Obserwacje',
    'Biological signals':'Sygnały biologiczne', 'Review & save':'Sprawdź i zapisz', 'Save observation':'Zapisz obserwację', 'Next →':'Dalej →', '← Back':'← Wstecz',
    'How will you provide it?':'Jak chcesz dodać dane?', 'Observation metadata':'Metadane obserwacji', 'Biological observation':'Obserwacja biologiczna',
    'NEW BIOLOGICAL OBSERVATION':'NOWA OBSERWACJA BIOLOGICZNA', 'EDIT BIOLOGICAL OBSERVATION':'EDYCJA OBSERWACJI BIOLOGICZNEJ', 'Upload file':'Prześlij plik',
    'Attach a local file to this observation':'Dołącz lokalny plik do tej obserwacji', 'Existing dataset':'Istniejący zbiór danych',
    'Reference an already registered dataset':'Wskaż wcześniej zarejestrowany zbiór danych', 'Manual entry':'Wpis ręczny', 'Create an observation without a file':'Utwórz obserwację bez pliku',
    'API import':'Import przez API', 'Paste structured JSON data':'Wklej uporządkowane dane JSON', 'Clinical/contextual record':'Rekord kliniczny / kontekstowy',
    'Spatial or methodological annotations':'Adnotacje przestrzenne lub metodologiczne', 'Research notes':'Notatki badawcze', 'Manual observation':'Obserwacja ręczna',
    'loading in background':'ładowanie w tle', 'loading':'ładowanie', 'ready':'gotowe', 'loaded':'załadowano', 'active':'aktywny', 'available on demand':'dostępna na żądanie',
    'no prepared evidence':'brak przygotowanych danych', 'mapping quality':'jakość mapowania',
    'No deeper target is defined here. Deeper biological resolution requires explicitly linked evidence.':'Nie zdefiniowano tu głębszego celu. Głębsza rozdzielczość biologiczna wymaga jawnie przypisanych danych.'
  }));
  const lower = new Map([...exact].map(([k,v]) => [k.toLowerCase(), v]));

  function translate(text) {
    if (!text) return text;
    let out = text;
    const trimmed = out.trim();
    if (exact.has(trimmed)) return out.replace(trimmed, exact.get(trimmed));
    if (lower.has(trimmed.toLowerCase())) return out.replace(trimmed, lower.get(trimmed.toLowerCase()));
    out = out.replace(/^(\d+)\s+macro observation(?:s)?\s+loaded$/i, (_,n) => `${n} ${n === '1' ? 'obserwacja makro' : 'obserwacji makro'} załadowano`);
    out = out.replace(/^(\d+)\s+view(?:s)?\s+available$/i, (_,n) => `${n} ${n === '1' ? 'dostępny widok' : 'dostępne widoki'}`);
    out = out.replace(/^(\d+)\s+macro evidence explicitly attached to\s+(.+)\.$/i, (_,n,r) => `${n} ${n === '1' ? 'dane makro jawnie przypisano' : 'danych makro jawnie przypisano'} do ${translate(r)}.`);
    out = out.replace(/^(\d+)\s+evidence item\(s\)$/i, (_,n) => `${n} ${n === '1' ? 'element danych' : 'elementów danych'}`);
    out = out.replace(/^Hand\s*>\s*Palm$/i, 'Dłoń > Śródręcze');
    out = out.replace(/^Hand\s*·\s*T0\s*·\s*Macro anatomy$/i, 'Dłoń · T0 · Anatomia makro');
    out = out.replace(/^Hand\s*·\s*T0\s*·\s*(.+)$/i, (_,x) => `Dłoń · T0 · ${translate(x)}`);
    out = out.replace(/^Macro\s*·\s*/i, 'Makro · '); out = out.replace(/^Tissue\s*·\s*/i, 'Tkanka · '); out = out.replace(/^Cellular\s*·\s*/i, 'Komórkowe · '); out = out.replace(/^Molecular\s*·\s*/i, 'Molekularne · ');
    out = out.replace(/^(.+)\s*·\s*no modality\s*·\s*(\d{4}-\d{2}-\d{2})\s*(.*)$/i, (_,a,d,r) => `${translate(a)} · Brak modalności · ${d}${r ? ` · ${translate(r)}` : ''}`);
    out = out.replace(/^Stage\s+(\d+)\s*·\s*(.+)$/i, (_,n,x) => `Etap ${n} · ${translate(x)}`);
    out = out.replace(/^no prepared evidence\s*·\s*mapping quality\s*([0-9.]+)$/i, (_,n) => `brak przygotowanych danych · jakość mapowania ${n.replace('.',',')}`);
    out = out.replace(/^Current spatial target:\s*(.+)$/i, (_,x) => `Bieżący cel przestrzenny: ${translate(x)}`);
    out = out.replace(/^Prepared assets in registry:\s*(.+)$/i, (_,x) => `Przygotowane zasoby w rejestrze: ${x}`);
    out = out.replace(/^coordinate space:\s*(.+)$/i, 'układ współrzędnych: $1');
    out = out.replace(/^view IDs are stable:\s*(.+)$/i, 'identyfikatory widoków są stabilne: $1');
    return out;
  }

  function skip(el) { return !el || el.closest('script,style,pre,code'); }
  function walk(root) {
    if (!root || skip(root)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => { if(skip(node.parentElement)) return; const value=node.nodeValue, trimmed=value.trim(); if(!trimmed) return; const translated=translate(trimmed); if(translated!==trimmed) node.nodeValue=value.replace(trimmed,translated); });
  }
  function translateAttributes(root=document) {
    root.querySelectorAll('[title],[aria-label],[alt]').forEach(el => { if(skip(el)) return; ['title','aria-label','alt'].forEach(attr => { if(!el.hasAttribute(attr)) return; const value=el.getAttribute(attr), translated=translate(value); if(translated!==value) el.setAttribute(attr,translated); }); });
  }
  let scheduled=false, mutating=false;
  function run(){ if(mutating) return; mutating=true; try{walk(document.body);translateAttributes();}finally{mutating=false;} }
  const observer=new MutationObserver(()=>{if(scheduled||mutating)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;run();});});
  function start(){run();observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','aria-label','alt']});window.dispatchEvent(new CustomEvent('testhp:i18n-ready',{detail:{locale:'pl'}}));}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true}); else start();
})();
