import { expect, test } from './_pipeline_guard';

test('customer reads transactions with separate dates and pending tags', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Transactions' }).first().click();

  await expect(page.getByRole('heading', { name: 'Transactions', level: 1 })).toBeVisible();
  const table = page.getByRole('table', { name: 'Account transactions' });
  await expect(table).toBeVisible();
  await expect(table.getByRole('columnheader', { name: 'Transaction time' })).toBeVisible();
  await expect(table.getByRole('columnheader', { name: 'Posted date' })).toBeVisible();
  await expect(table.getByText('Status: Pending').first()).toBeVisible();
  await expect(table.getByText('Status: Posted').first()).toBeVisible();
  await expect(table.getByText('unconfirmed freshness').first()).toBeVisible();
  await expect(table.getByText('**** 4821').first()).toBeVisible();
  await expect(page.getByText('Pending is not posted')).toBeVisible();
});
