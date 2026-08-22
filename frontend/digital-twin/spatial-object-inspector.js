(() => {
  function escape(value) {
    return String(value ?? '').replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  }

  function render(container, object) {
    if (!container) return;
    if (!object) { container.textContent = 'No spatial object selected.'; return; }
    const quality = object.quality || {};
    container.innerHTML = `<div class="spatial-object-inspector">
      <strong>${escape(object.object_type || 'Spatial object')}</strong>
      <div>ID: <code>${escape(object.spatial_object_id)}</code></div>
      <div>Source: ${escape(object.source || '—')}</div>
      <div>Coordinate system: ${escape(object.coordinate_system || '—')}</div>
      <div>Status: ${escape(object.metadata?.status || '—')}</div>
      <div>Quality: ${escape(quality.overall ?? quality.status ?? '—')}</div>
    </div>`;
  }

  window.SpatialObjectInspector = { render };
})();
