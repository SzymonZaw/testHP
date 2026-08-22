(() => {
  const state = { selectedObjectId: null, focusRequest: null };
  window.SpatialNavigationAdapter = {
    select(spatialObjectId) { state.selectedObjectId = spatialObjectId || null; window.dispatchEvent(new CustomEvent('spatial-object-selected', { detail: { spatialObjectId: state.selectedObjectId } })); },
    focus(spatialObjectId) { state.focusRequest = spatialObjectId || null; window.dispatchEvent(new CustomEvent('spatial-object-focus', { detail: { spatialObjectId: state.focusRequest } })); },
    getState() { return { ...state }; }
  };
})();
