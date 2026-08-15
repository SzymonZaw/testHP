(() => {
  const status = document.getElementById('system-status');
  if (!status) return;
  window.addEventListener('error', event => {
    const message = event?.error?.message || event?.message || 'Unknown frontend error';
    status.textContent = `Checking system · frontend error: ${message}`;
    status.title = status.textContent;
  });
  window.addEventListener('unhandledrejection', event => {
    const reason = event?.reason?.message || String(event?.reason || 'Unknown promise rejection');
    status.textContent = `Checking system · frontend error: ${reason}`;
    status.title = status.textContent;
  });
})();
