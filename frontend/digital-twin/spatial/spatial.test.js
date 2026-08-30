import test from "node:test";
import assert from "node:assert/strict";
import { createSpatialAsset, createCoordinateSystem, createSpatialSource } from "./spatial-types.js";
import { validateSpatialAsset, validateCoordinateSystem, validateSpatialSource } from "./spatial-validator.js";
import { SpatialDataAdapter } from "./spatial-data-adapter.js";
import { applySpatialSelection, createSpatialCanonicalState, restoreSpatialState, serializeSpatialState } from "./spatial-state.js";
import { buildRegionEvidenceIndex, getEvidenceForSpatialSelection } from "./spatial-evidence.js";

const regions = ["palm", "thumb", "index", "middle", "ring", "little", "wrist"].map((id) => ({
  id,
  geometryId: `geometry:${id}`,
}));

const fixture = {
  source: createSpatialSource({ id: "fixture-source", type: "own_dataset" }),
  coordinateSystem: createCoordinateSystem({ id: "canonical-hand-v1", units: "mm" }),
  asset: createSpatialAsset({ id: "fixture-hand", sourceId: "fixture-source", coordinateSystemId: "canonical-hand-v1", regions }),
};

test("validates complete spatial hand asset", () => {
  assert.equal(validateSpatialSource(fixture.source).valid, true);
  assert.equal(validateCoordinateSystem(fixture.coordinateSystem).valid, true);
  assert.equal(validateSpatialAsset(fixture.asset).valid, true);
});

test("maps geometry id to region id", () => {
  const adapter = new SpatialDataAdapter(fixture);
  assert.equal(adapter.getRegionByGeometryId("geometry:palm").id, "palm");
});

test("selection updates only spatial canonical fields", () => {
  const state = createSpatialCanonicalState({ subject: "own_cohort", timepoint: "T0" });
  const next = applySpatialSelection(state, { regionId: "palm", tissueId: "connective_tissue", cellId: "A17" });
  assert.deepEqual(next, { ...state, region: "palm", tissue: "connective_tissue", cell: "A17" });
});

test("canonical state survives serialization and restore", () => {
  const state = createSpatialCanonicalState({ subject: "own_cohort", timepoint: "T1", region: "thumb" });
  assert.deepEqual(restoreSpatialState(serializeSpatialState(state)), state);
});

test("evidence is scoped to the spatial selection", () => {
  const evidence = [
    { id: "img-palm", regionId: "palm", timepointId: "T0" },
    { id: "img-thumb", regionId: "thumb", timepointId: "T0" },
  ];
  const index = buildRegionEvidenceIndex(evidence);
  assert.equal(index.get("palm").length, 1);
  assert.equal(getEvidenceForSpatialSelection(evidence, { regionId: "palm", timepointId: "T0" }).length, 1);
});
