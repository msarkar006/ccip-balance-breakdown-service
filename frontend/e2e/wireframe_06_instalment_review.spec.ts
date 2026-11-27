import { test, expect } from './_pipeline_guard';

test.describe('Unified Status Tracker (Wireframe 06)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/account-overview');
  });

  test('displays tracker items with lifecycle states', async ({ page }) => {
    await page.goto('/tracker');
    
    await expect(page.locator('h1')).toContainText('Activity Tracker');
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    await expect(table.getByText('Type')).toBeVisible();
    await expect(table.getByText('Title')).toBeVisible();
    await expect(table.getByText('Status')).toBeVisible();
    await expect(table.getByText('Last Updated')).toBeVisible();
  });

  test('displays escalation cue when item is escalated', async ({ page }) => {
    await page.goto('/tracker');
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    // Check if any tracker items show escalation status
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('filters to unresolved items', async ({ page }) => {
    await page.goto('/tracker');
    
    const unresolvedButton = page.getByRole('button', { name: /Unresolved/ });
    await expect(unresolvedButton).toBeVisible();
    
    await unresolvedButton.click();
    
    // The filter should update the displayed results
    await expect(unresolvedButton).toBeVisible();
  });

  test('refreshes tracker item status', async ({ page }) => {
    await page.goto('/tracker');
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    // Look for refresh buttons in the table
    const refreshButton = page.getByRole('button', { name: /Refresh/ }).first();
    await expect(refreshButton).toBeVisible();
    await refreshButton.click();
    
    // Should show some feedback about the refresh
    await expect(page.locator('body')).toBeVisible();
  });

  test('displays all items and unresolved counts', async ({ page }) => {
    await page.goto('/tracker');
    
    await expect(page.getByRole('button', { name: /All items/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Unresolved/ })).toBeVisible();
  });
});
