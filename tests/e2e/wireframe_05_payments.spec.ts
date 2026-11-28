import { expect, test } from './_pipeline_guard';

test('customer reads payment records with source status and informational notice', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Payments' }).first().click();

  await expect(page.getByRole('heading', { name: 'Payments', level: 1 })).toBeVisible();
  const table = page.getByRole('table', { name: 'Payment history' });
  await expect(table).toBeVisible();
  await expect(table.getByText('PMT-1', { exact: true })).toBeVisible();
  await expect(table.getByText('Status: Completed').first()).toBeVisible();
  await expect(table.getByText('Type: OneOff').first()).toBeVisible();
  await expect(table.getByText('****1234').first()).toBeVisible();
  await expect(page.getByText('freshness unavailable').first()).toBeVisible();
  await expect(page.getByRole('button', { name: /^View record PMT-1$/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /make|schedule|cancel|amend/i })).toHaveCount(0);
});
