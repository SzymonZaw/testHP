(() => {
  const status = document.getElementById('system-status');
  const show = message => {
    if (!status) return;
    status.textContent = message;
    status.title = message;
  };

  const script = document.createElement('script');
  script.src = `/assets/app4.js?v=real-analyses-6&t=${Date.now()}`;
  script.onload = () => {
    if (window.__HPP_DASHBOARD_STARTED__) return;
    show('Checking system · dashboard script loaded but did not start');
  };
  script.onerror = () => {
    show(`Checking system · dashboard script failed to load: ${script.src}`);
  };
  document.body.appendChild(script);
})();
