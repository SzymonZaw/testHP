(() => {
  const replacements = new Map([
    ['INTERPRETACJA BADAWCZA', 'INTERPRETACJA BADAWCZA'],
    ['STAN BIOLOGICZNY', 'STAN BIOLOGICZNY'],
    ['RESEARCH ONLY', 'TYLKO DO BADAŃ'],
    ['HIERARCHICAL SUMMARY', 'PODSUMOWANIE HIERARCHICZNE'],
    ['MACRO → TISSUE → CELLULAR → CELL', 'MAKRO → TKANKA → KOMÓRKOWE → KOMÓRKA'],
    ['STAGE 4', 'ETAP 4'],
    ['Observed', 'Dane obserwowane'],
    ['Observed ·', 'Dane obserwowane ·'],
    ['Insufficient evidence', 'Niewystarczające dane'],
    ['evidence item(s)', 'elementów danych'],
    ['evidence item', 'element danych'],
    ['Parent summaries aggregate only explicitly attached descendant evidence. They never create evidence where none exists.', 'Podsumowania nadrzędne uwzględniają wyłącznie jawnie przypisane dane elementów potomnych. Nie tworzą danych, jeśli takie dane nie istnieją.'],
    ['No established conclusion', 'Brak ustalonego wniosku'],
    ['Requires validated data', 'Wymaga zwalidowanych danych'],
    ['Not assessed from current data', 'Nieocenione na podstawie bieżących danych'],
    ['No diagnostic inference', 'Brak wnioskowania diagnostycznego'],
    ['Data', 'Dane'],
    ['Data availability', 'Dostępność danych'],
    ['Confidence', 'Pewność'],
    ['0 items', '0 elementów'],
  ]);

  function translateText(value) {
    let out = value;
    for (const [from, to] of replacements) out = out.replaceAll(from, to);
    return out;
  }

  function translateNode(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const next = translateText(node.nodeValue || '');
      if (next !== node.nodeValue) node.nodeValue = next;
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.tagName === 'SCRIPT' || node.tagName === 'STYLE') return;
    for (const child of node.childNodes) translateNode(child);
  }

  function run() {
    translateNode(document.body);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }

  const observer = new MutationObserver(mutations => {
    observer.disconnect();
    for (const mutation of mutations) {
      if (mutation.type === 'characterData') translateNode(mutation.target);
      for (const node of mutation.addedNodes) translateNode(node);
    }
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  });

  const startObserver = () => observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  if (document.body) startObserver();
  else document.addEventListener('DOMContentLoaded', startObserver, { once: true });
})();
