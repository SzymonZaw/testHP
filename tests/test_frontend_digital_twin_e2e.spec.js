import { test, expect } from '@playwright/test';

test('synthetic Digital Twin cell assessment flows into frontend inspector', async ({ page }) => {
  await page.goto('/digital-twin/');
  await expect(page.locator('#twin-viewport')).toBeVisible();
  await expect.poll(async () => page.evaluate(() => Boolean(window.testhpSyntheticE2E?.cells?.length))).toBeTruthy();

  const fixture = await page.evaluate(() => window.testhpSyntheticE2E);
  expect(fixture.summary.cellCount).toBe(1000);
  expect(fixture.summary.investigateCount).toBe(50);

  const worsening = fixture.cells.find((cell) => cell.priority === 'investigate');
  expect(worsening).toBeTruthy();
  expect(worsening.timeline.T0.abnormalityScore).toBe(0.45);
  expect(worsening.timeline.T2.abnormalityScore).toBe(0.75);

  await page.evaluate((cell) => {
    const target = {
      level: 'cellular',
      spatial_id: cell.cellId,
      label: cell.cellId,
      region_id: cell.regionId,
      tissue_id: cell.tissueId,
    };
    window.dispatchEvent(new CustomEvent('testhp:spatial-contract-changed', { detail: target }));
    const set = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
    const panel = document.getElementById('cell-assessment-panel');
    if (panel) panel.hidden = false;
    set('cell-assessment-health', cell.assessment.healthState);
    set('cell-assessment-age', String(cell.assessment.biologicalAge));
    set('cell-assessment-abnormality', String(cell.assessment.abnormalityScore));
    set('cell-assessment-uncertainty', String(cell.assessment.uncertainty));
    set('cell-assessment-trend', `Trend: abnormality +${(cell.timeline.T2.abnormalityScore - cell.timeline.T0.abnormalityScore).toFixed(2)}`);
    set('cell-assessment-priority', `Priorytet obserwacyjny: ${cell.priority}`);
    set('cell-assessment-evidence', `Evidence: ${cell.assessment.evidenceCount}`);
  }, worsening);

  await expect(page.locator('#cell-assessment-panel')).toBeVisible();
  await expect(page.locator('#cell-assessment-health')).toHaveText('abnormal');
  await expect(page.locator('#cell-assessment-age')).toHaveText('44');
  await expect(page.locator('#cell-assessment-abnormality')).toHaveText('0.75');
  await expect(page.locator('#cell-assessment-priority')).toHaveText('Priorytet obserwacyjny: investigate');
  await expect(page.locator('#cell-assessment-trend')).toHaveText('Trend: abnormality +0.30');
});
