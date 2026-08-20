(() => {
  const HELP_HTML = `
    <strong>Wybrany region</strong>
    Ten panel pokazuje wszystkie dane przypisane bezpośrednio do zaznaczonego regionu cyfrowego bliźniaka.<br><br>
    Możesz dodawać, edytować i usuwać:<br>
    • zdjęcia makro,<br>
    • dane tkankowe,<br>
    • dane komórkowe,<br>
    • dane molekularne.<br><br>
    Wszystkie przypisane dane są powiązane z aktualnie wybranym regionem i mogą być wykorzystane przez Nawigację Przestrzenną oraz Cyfrowego Bliźniaka 3D.
  `;

  function cleanup() {
    // The spatial navigator and the 3D twin already establish the selected region.
    document.querySelectorAll('#zoom-region, [data-action="zoom-region"], .zoom-region, button').forEach((el) => {
      if (el.id === 'zoom-region' || el.textContent?.trim().toLowerCase().includes('skup na regionie')) {
        el.remove();
      }
    });

    // Remove the obsolete static pipeline presentation from the Region Inspector.
    document.querySelectorAll('.ri-workflow').forEach((el) => el.remove());
    document.querySelectorAll('*').forEach((el) => {
      if (el.children.length === 0 && el.textContent?.trim().startsWith('Przepływ danych')) {
        el.closest('.ri-workflow')?.remove();
      }
    });

    // Replace the help copy so it describes the current frontend capabilities.
    document.querySelectorAll('.ri-help').forEach((el) => {
      if (!el.dataset.currentHelp) {
        el.innerHTML = HELP_HTML;
        el.dataset.currentHelp = '1';
      }
    });
  }

  cleanup();
  const observer = new MutationObserver(cleanup);
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener('load', cleanup, { once: true });
})();
