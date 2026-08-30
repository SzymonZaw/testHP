(() => {
  'use strict';
  const load = async () => {
    if (!window.__testhpDigitalTwinEndUserUIV1) return;
    const params = new URLSearchParams(window.location.search);
    const subjectId = params.get('subject_id') || 'own_cohort';
    const timepoint = params.get('timepoint') || 'T0';
    try {
      const response = await fetch(`/api/hand/analysis?subject_id=${encodeURIComponent(subjectId)}&timepoint=${encodeURIComponent(timepoint)}`);
      if (!response.ok) return;
      const analysis = await response.json();
      window.__testhpLastAnalysis = analysis;
      window.__testhpDigitalTwinEndUserUIV1.setAnalysis(analysis);
      window.dispatchEvent(new CustomEvent('testhp:end-user-analysis-loaded', { detail: { subjectId, timepoint } }));
    } catch (error) {
      console.warn('End-user analysis unavailable', error);
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', load); else load();
})();
