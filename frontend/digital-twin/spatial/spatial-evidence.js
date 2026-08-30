export function createEvidenceReference(input = {}) {
  return {
    id: input.id,
    modality: input.modality,
    status: input.status || "missing",
    subjectId: input.subjectId,
    timepointId: input.timepointId,
    regionId: input.regionId,
    tissueId: input.tissueId,
    cellId: input.cellId,
    quality: input.quality,
    source: input.source,
    provenance: input.provenance,
  };
}

export function buildRegionEvidenceIndex(evidence = []) {
  const index = new Map();
  for (const item of evidence) {
    if (!item?.regionId) continue;
    if (!index.has(item.regionId)) index.set(item.regionId, []);
    index.get(item.regionId).push(createEvidenceReference(item));
  }
  return index;
}

export function getEvidenceForRegion(evidenceIndex, regionId) {
  return evidenceIndex?.get(regionId) || [];
}

export function getEvidenceForSpatialSelection(evidence = [], selection = {}) {
  return evidence.filter((item) => {
    if (selection.subjectId && item.subjectId !== selection.subjectId) return false;
    if (selection.timepointId && item.timepointId !== selection.timepointId) return false;
    if (selection.regionId && item.regionId !== selection.regionId) return false;
    if (selection.tissueId && item.tissueId !== selection.tissueId) return false;
    if (selection.cellId && item.cellId !== selection.cellId) return false;
    return true;
  });
}
