document.addEventListener('DOMContentLoaded', () => {
  const status = document.getElementById('system-status');
  if (status) status.textContent = 'System ready';
  const script = document.createElement('script');
  script.src = '/assets/app4.js?v=0.6.1';
  script.async = true;
  document.body.appendChild(script);
});
