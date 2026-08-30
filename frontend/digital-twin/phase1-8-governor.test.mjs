import assert from 'node:assert/strict';
import test from 'node:test';
import { createDigitalTwinState } from './canonical-state.js';
import {
  NOT_ESTABLISHED,
  canonicalSpatialTree,
  sanitizeSelection,
  suppliedCells,
  suppliedMolecularLayers,
  suppliedTissues,
} from './digital-twin-phase1-8-governor.js';

function stateWithAnatomy() {
  return createDigitalTwinState({
    anatomy: {
      hand: { id: 'hand-001' },
      regions: [{ id: 'palm' }],
      tissues: [{ tissue_id: 'connective-1', name: 'Connective tissue', region_id: 'palm' }],
      cells: [
        { cell_id: 'A17', type: 'Fibroblast', region_id: 'palm', tissue_id: 'connective-1' },
        { cell_id: 'A18', type: 'Fibroblast', region_id: 'palm', tissue_id: 'connective-1' },
      ],
    },
    molecular: { states: [{ cell_id: 'A17', layer: 'rna' }] },
  });
}

test('canonical initialization contains the phase 1 state dimensions', () => {
  const state = createDigitalTwinState();
  assert.deepEqual(state.selection, {
    subject: 'own_cohort', timepoint: 'T0', region: 'palm', tissue: null, cell: null, molecularLayer: null,
  });
  assert.ok(state.evidence);
  assert.ok(state.biologicalState);
  assert.equal(state.biologicalState.status, NOT_ESTABLISHED);
});

test('spatial tree contains only supplied tissues and cells', () => {
  const state = stateWithAnatomy();
  const tree = canonicalSpatialTree(state);
  const palm = tree.regions.find((region) => region.id === 'palm');
  assert.equal(palm.tissues.length, 1);
  assert.equal(palm.tissues[0].id, 'connective-1');
  assert.deepEqual(palm.tissues[0].cells.map((cell) => cell.id), ['A17', 'A18']);
});

test('missing tissue or cell is not selectable', () => {
  const state = stateWithAnatomy();
  assert.equal(suppliedTissues(state, 'thumb').length, 0);
  assert.equal(suppliedCells(state, 'palm', 'missing-tissue').length, 0);
  const safe = sanitizeSelection(state, { tissue: 'missing-tissue', cell: 'fake-cell' });
  assert.equal(safe.selection.tissue, null);
  assert.equal(safe.selection.cell, null);
});

test('molecular layers are scoped to the selected cell', () => {
  const state = stateWithAnatomy();
  assert.deepEqual(suppliedMolecularLayers(state, 'A17').map((item) => item.id), ['rna']);
  assert.deepEqual(suppliedMolecularLayers(state, 'A18'), []);
});

test('partial backend data never becomes clinical confidence', () => {
  const state = createDigitalTwinState({ evidence: { coverage: 0.125, confidence: null, missingModalities: ['rna'] } });
  assert.equal(state.evidence.coverage, 0.125);
  assert.equal(state.evidence.confidence, null);
  assert.equal(state.biologicalState.status, NOT_ESTABLISHED);
});
