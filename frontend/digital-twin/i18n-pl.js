(() => {
  const exact = new Map(Object.entries({
    'Digital Twin · boot diagnostics':'Cyfrowy bliźniak · diagnostyka uruchomienia',
    'Digital Twin ready':'Cyfrowy bliźniak gotowy',
    'Twin Viewport error':'Błąd widoku cyfrowego bliźniaka',
    'Three.js + canonical viewport':'Three.js + kanoniczny widok',
    'app.js loaded':'app.js załadowany',
    'Spatial bridge':'Most przestrzenny',
    'loaded':'załadowano',
    'Evidence renderer':'Renderer danych',
    'Viewport debug':'Diagnostyka widoku',
    'Evidence registry':'Rejestr danych',
    'Spatial stages 2–4':'Etapy przestrzenne 2–4',
    'Stages 5–8':'Etapy 5–8',
    'loaded asynchronously':'załadowano asynchronicznie',
    'Evidence UX':'Obsługa danych',
    'Deep drill':'Analiza pogłębiona',
    'Viewport boot verifier':'Weryfikator uruchomienia widoku',
    'active':'aktywny',
    'Hand surface stages 11–15':'Etapy powierzchni dłoni 11–15',
    'Hand surface edit bridge':'Most edycji powierzchni dłoni',
    'Hand surface stages 20–22':'Etapy powierzchni dłoni 20–22',
    'Photo reconstruction':'Rekonstrukcja ze zdjęć',
    'available on demand':'dostępna na żądanie',
    'Heavy modules are loaded only after the canonical viewport is ready.':'Ciężkie moduły są ładowane dopiero po przygotowaniu kanonicznego widoku.',
    'Enable photo reconstruction':'Włącz rekonstrukcję ze zdjęć',
    'Macro anatomy':'Anatomia makro',
    'Tissue field':'Pole tkankowe',
    'Cellular field':'Pole komórkowe',
    'Single cell':'Pojedyncza komórka',
    'spatial target':'cel przestrzenny',
    'navigation only':'tylko nawigacja',
    'Finest spatial target':'Najbardziej szczegółowy cel przestrzenny',
    'No deeper target is defined here. Deeper biological resolution requires explicitly linked evidence.':'Nie zdefiniowano tu głębszego celu. Głębsza rozdzielczość biologiczna wymaga jawnie przypisanych danych.',
    'Hand':'Dłoń',
    'Palm':'Śródręcze',
    'Wrist':'Nadgarstek',
    'Thumb':'Kciuk',
    'Index finger':'Palec wskazujący',
    'Middle finger':'Palec środkowy',
    'Ring finger':'Palec serdeczny',
    'Little finger':'Mały palec',
    'Thenar eminence':'Kłąb kciuka',
    'Hypothenar eminence':'Kłębik dłoni',
    'Central palm':'Centralna część dłoni',
    'Proximal segment':'Odcinek bliższy',
    'Middle segment':'Odcinek środkowy',
    'Distal segment':'Odcinek dalszy',
    'Microscopy field A':'Pole mikroskopowe A',
    'Microscopy field B':'Pole mikroskopowe B',
    'Microscopy field C':'Pole mikroskopowe C',
    'Cell target 1':'Cel komórkowy 1',
    'Cell target 2':'Cel komórkowy 2',
    'Cell target 3':'Cel komórkowy 3',
    'OBSERVED':'OBSERWOWANE',
    'NONE':'BRAK',
    'PARENT':'NADRZĘDNE',
    'REGION':'REGION',
    'LINKED':'PRZYPISANE',
    'Unavailable':'Niedostępne',
    'No evidence':'Brak danych',
    'Not shown at this resolution':'Nieprezentowane na tym poziomie',
    'Parent evidence only':'Tylko dane z regionu nadrzędnego',
    'Linked evidence':'Przypisane dane',
    'Navigation only':'Tylko nawigacja',
    'No modality':'Brak modalności',
    'No tissue / WSI evidence is explicitly linked to this region.':'Brak danych tkankowych / WSI jawnie przypisanych do tego regionu.',
    'No tissue / WSI evidence is linked to this target. The node remains navigation only.':'Brak danych tkankowych / WSI przypisanych do tego celu. Węzeł pozostaje wyłącznie nawigacyjny.',
    'Cellular evidence requires explicitly linked microscopy data.':'Dane komórkowe wymagają jawnie przypisanych danych mikroskopowych.',
    'No cellular evidence is linked to this field. The visualization is a navigation target only.':'Brak danych komórkowych przypisanych do tego pola. Wizualizacja jest wyłącznie celem nawigacyjnym.',
    'No molecular measurements are explicitly linked to this region.':'Brak pomiarów molekularnych jawnie przypisanych do tego regionu.',
    'Evidence layer':'Warstwa danych',
    'Anatomy':'Anatomia',
    'Anatomical structure':'Struktura anatomiczna',
    'Progressive resolution':'Postępująca rozdzielczość',
    'Progressive biological resolution':'Postępująca rozdzielczość biologiczna',
    'Longitudinal':'Podłużna historia',
    'Longitudinal twin':'Bliźniak w czasie',
    'RESEARCH ONLY':'TYLKO DO BADAŃ',
    'Stage 5 · spatially attached observations':'Etap 5 · dane przypisane przestrzennie',
    'Stage 6 · depth context':'Etap 6 · kontekst głębokości',
    'Stage 7 · context preserved':'Etap 7 · zachowany kontekst',
    'Stage 8 · time-aware twin':'Etap 8 · bliźniak uwzględniający czas',
    'Evidence is explicit research data; navigation targets do not imply biological findings.':'Dane są jawnymi danymi badawczymi; cele nawigacyjne nie oznaczają ustaleń biologicznych.',
    'Observation data':'Dane obserwacji',
    'Add observation':'Dodaj obserwację',
    'Edit':'Edytuj',
    'Remove':'Usuń',
    'Details':'Szczegóły',
    'Archive':'Archiwizuj',
    'All':'Wszystkie',
    'Archived':'Zarchiwizowane',
    'Stage 11 contract':'Kontrakt etapu 11',
    'one spatial target per observation':'jeden cel przestrzenny dla każdej obserwacji',
    'editable metadata and notes':'edytowalne metadane i notatki',
    'archive instead of destructive loss':'archiwizacja zamiast nieodwracalnego usuwania',
    'provenance history stays with the record':'historia pochodzenia pozostaje przy rekordzie',
    'Prepare image':'Przygotowanie obrazu',
    'Natural geometry':'Naturalna geometria',
    'Surface mapping':'Mapowanie powierzchni',
    'Workflow':'Przepływ pracy',
    'Real images → prepared surface → registration':'Prawdziwe zdjęcia → przygotowana powierzchnia → rejestracja',
    'Stage 12 · Image preparation':'Etap 12 · przygotowanie obrazu',
    'Prepare the photo before any surface projection. The original file is never modified.':'Przygotuj zdjęcie przed projekcją na powierzchnię. Oryginalny plik nigdy nie jest modyfikowany.',
    'Background tolerance':'Tolerancja tła',
    'Max dimension':'Maksymalny wymiar',
    'Waiting for an image.':'Oczekiwanie na obraz.',
    'Choose a skin photo.':'Wybierz zdjęcie skóry.',
    'Prepare image':'Przygotuj obraz',
    'Save prepared asset':'Zapisz przygotowany zasób',
    'Stage 13 · Natural hand geometry':'Etap 13 · naturalna geometria dłoni',
    'Palm length':'Długość dłoni',
    'Palm width':'Szerokość dłoni',
    'Finger spread':'Rozstaw palców',
    'Thumb angle':'Kąt kciuka',
    'Finger taper':'Zwężanie palców',
    'Surface thickness':'Grubość powierzchni',
    'Naturalization rules':'Zasady naturalizacji',
    'Apply to 3D surface':'Zastosuj do powierzchni 3D',
    'Reset':'Resetuj',
    'Stage 14 · Surface mapping':'Etap 14 · mapowanie powierzchni',
    'Registration quality':'Jakość rejestracji',
    'Coordinate system:':'Układ współrzędnych:',
    'Save registration':'Zapisz rejestrację',
    'Registered views':'Zarejestrowane widoki',
    'Stage 15 · Workflow':'Etap 15 · przepływ pracy',
    'HAND SURFACE PIPELINE':'POTOK POWIERZCHNI DŁONI',
    'registration → projection plan → exportable twin package':'rejestracja → plan projekcji → pakiet bliźniaka do eksportu',
    'Registration QA':'Kontrola jakości rejestracji',
    'Projection plan':'Plan projekcji',
    'Twin package':'Pakiet bliźniaka',
    'Stage 20 · Registration QA':'Etap 20 · kontrola jakości rejestracji',
    'Checks the five intended views before any real multi-view projection. This stage does not pretend that registration is clinically accurate.':'Sprawdza pięć zamierzonych widoków przed właściwą projekcją wielowidokową. Ten etap nie zakłada klinicznej dokładności rejestracji.',
    'Registration contract':'Kontrakt rejestracji',
    'quality is explicit and editable':'jakość jest jawna i edytowalna',
    'missing views remain missing; no synthetic evidence is invented':'brakujące widoki pozostają brakujące; nie tworzymy sztucznych danych',
    'Recheck':'Sprawdź ponownie',
    'Open Stage 14':'Otwórz etap 14',
    'Stage 21 · Projection plan':'Etap 21 · plan projekcji',
    'Rebuild plan':'Przebuduj plan',
    'Save plan':'Zapisz plan',
    'Projection rules':'Zasady projekcji',
    'Stage 22 · Twin package':'Etap 22 · pakiet bliźniaka',
    'Export package JSON':'Eksportuj pakiet JSON',
    'Refresh validation':'Odśwież walidację',
    'READY FOR TESTING':'GOTOWE DO TESTÓW',
    'REVIEW REQUIRED':'WYMAGA WERYFIKACJI',
    'Evidence management':'Zarządzanie danymi',
    'Observations':'Obserwacje',
    'Biological signals':'Sygnały biologiczne',
    'Review & save':'Sprawdź i zapisz',
    'Save observation':'Zapisz obserwację',
    'Next →':'Dalej →',
    '← Back':'← Wstecz',
    'How will you provide it?':'Jak chcesz dodać dane?',
    'Observation metadata':'Metadane obserwacji',
    'Biological observation':'Obserwacja biologiczna',
    'NEW BIOLOGICAL OBSERVATION':'NOWA OBSERWACJA BIOLOGICZNA',
    'EDIT BIOLOGICAL OBSERVATION':'EDYCJA OBSERWACJI BIOLOGICZNEJ',
    'Upload file':'Prześlij plik',
    'Attach a local file to this observation':'Dołącz lokalny plik do tej obserwacji',
    'Existing dataset':'Istniejący zbiór danych',
    'Reference an already registered dataset':'Wskaż wcześniej zarejestrowany zbiór danych',
    'Manual entry':'Wpis ręczny',
    'Create an observation without a file':'Utwórz obserwację bez pliku',
    'API import':'Import przez API',
    'Paste structured JSON data':'Wklej uporządkowane dane JSON',
    'Clinical/contextual record':'Rekord kliniczny / kontekstowy',
    'Spatial or methodological annotations':'Adnotacje przestrzenne lub metodologiczne',
    'Research notes':'Notatki badawcze',
    'Manual observation':'Obserwacja ręczna',
    'Details':'Szczegóły',
    'unknown':'nieznane'
  }));

  function translate(text) {
    if (!text) return text;
    if (exact.has(text)) return exact.get(text);
    let out = text;
    out = out.replace(/^(\d+) macro observation(s)? loaded$/i, '$1 obserwacj$2 makro załadowano');
    out = out.replace(/^(\d+) view(s)? available$/i, '$1 dostępn$2 widoków');
    out = out.replace(/^(\d+) macro evidence explicitly attached to (.+)\.$/i, '$1 danych makro jawnie przypisano do $2.');
    out = out.replace(/^Hand · T0 · Macro anatomy$/i, 'Dłoń · T0 · Anatomia makro');
    out = out.replace(/^Hand · T0 · (.+)$/i, 'Dłoń · T0 · $1');
    out = out.replace(/^(.+) · (hand|tissue|macro|cellular|molecular)$/i, (m, a, b) => `${a} · ${translate(b)}`);
    out = out.replace(/^(.+) · no modality · (\d{4}-\d{2}-\d{2}) · (.+)$/i, '$1 · brak modalności · $2 · $3');
    out = out.replace(/^Stage (\d+) · /i, 'Etap $1 · ');
    out = out.replace(/^Macro · /i, 'Makro · ');
    out = out.replace(/^Tissue · /i, 'Tkanka · ');
    out = out.replace(/^Cellular · /i, 'Komórkowe · ');
    out = out.replace(/^Molecular · /i, 'Molekularne · ');
    out = out.replace(/^Real linked data$/i, 'Rzeczywiście przypisane dane');
    return out;
  }

  function shouldSkip(node) {
    const el = node.parentElement;
    if (!el) return true;
    if (el.closest('script,style,pre,code')) return true;
    if (el.closest('#twin-viewport-debug-host')) return true;
    // Keep internal spatial-navigation strings intact because the navigation
    // engine uses their English identifiers as stable machine-readable labels.
    if (el.closest('.spatial-navigator')) return true;
    return false;
  }

  function walk(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      if (shouldSkip(node)) return;
      const value = node.nodeValue;
      const trimmed = value.trim();
      if (!trimmed) return;
      const translated = translate(trimmed);
      if (translated !== trimmed) node.nodeValue = value.replace(trimmed, translated);
    });
  }

  function translateAttributes() {
    document.querySelectorAll('[title],[aria-label],[alt]').forEach(el => {
      if (el.closest('script,style')) return;
      ['title','aria-label','alt'].forEach(attr => {
        if (!el.hasAttribute(attr)) return;
        const value = el.getAttribute(attr);
        const translated = translate(value);
        if (translated !== value) el.setAttribute(attr, translated);
      });
    });
  }

  let scheduled = false;
  const run = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      walk(document.body);
      translateAttributes();
    });
  };

  const observer = new MutationObserver(run);
  const start = () => {
    run();
    observer.observe(document.body, {subtree:true, childList:true, characterData:true});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
