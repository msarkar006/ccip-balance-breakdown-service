import { expect, test } from './_pipeline_guard';

test('customer sees the account overview with its card and a link to the breakdown', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Account overview', level: 1 })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Synthetic Everyday Card' })).toBeVisible();
  await expect(page.getByText('Account status: Open')).toBeVisible();
  for (const label of ['Credit limit', 'Available credit', 'Current balance', 'Statement balance', 'Minimum payment', 'Standard purchase APR', 'Next statement date', 'Payment due date']) {
    await expect(page.getByText(label, { exact: true })).toBeVisible();
  }
  await expect(page.getByLabel('Account', { exact: true })).toBeVisible();
  await expect(page.getByText('£10,000.00')).toBeVisible();
  await expect(page.getByText('freshness unavailable')).toBeVisible();
  await expect(page.getByText('Card status: Active')).toBeVisible();
  await expect(page.getByText('**** 4821')).toBeVisible();
  await page.getByRole('link', { name: 'View dated balance breakdown' }).click();
  await expect(page.getByRole('heading', { name: 'Dated balance breakdown', level: 1 })).toBeVisible();
});
