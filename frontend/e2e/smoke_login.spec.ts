import { test, expect } from './_pipeline_guard';

test('smoke test - login page loads and has correct title', async ({ page }) => {
  await page.goto('/login');
  await expect(page).toHaveTitle(/CCIP Balance Breakdown Service/);
  await expect(page.locator('h1')).toContainText(/log in to your credit card account/i);
});
