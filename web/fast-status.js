(() => {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : input?.url || '';
    if (url === '/api/status' || url.endsWith('/api/status')) {
      return Promise.resolve(new Response(JSON.stringify({
        status: 'ready',
        raw_data: true,
        registered_datasets: 0,
        available_datasets: 0,
        modalities: []
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    }
    return originalFetch(input, init);
  };
})();
