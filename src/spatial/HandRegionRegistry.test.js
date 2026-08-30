import { createHandRegionRegistry, mapGeometryToRegion, validateHandRegionRegistry } from './HandRegionRegistry.js';

test('requires all canonical hand regions and unique geometry mappings', () => {
  const registry = createHandRegionRegistry([
    ...['palm', 'thumb', 'index', 'middle', 'ring', 'little', 'wrist'].map((regionId, i) => ({ regionId, geometryIds: [`g${i}`] }))
  ]);
  expect(validateHandRegionRegistry(registry).valid).toBe(true);
  expect(mapGeometryToRegion(registry, 'g3')).toBe('middle');
  expect(mapGeometryToRegion(registry, 'missing')).toBeNull();
});

test('rejects duplicate and ambiguous geometry mappings', () => {
  const registry = createHandRegionRegistry([
    { regionId: 'palm', geometryIds: ['shared'] },
    { regionId: 'thumb', geometryIds: ['shared'] },
  ]);
  expect(registry.errors).toContain('Region has no geometryIds: index');
  expect(() => mapGeometryToRegion(registry, 'shared')).toThrow('Ambiguous geometryId mapping');
});
