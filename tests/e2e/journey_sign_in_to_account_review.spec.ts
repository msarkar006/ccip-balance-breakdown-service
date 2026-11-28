import { expect, test } from './_pipeline_guard';

test('customer01 reviews account, balance breakdown, transactions and payments', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Account overview
  await expect(page.getByRole('heading', { name: 'Account overview', level: 1 })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Synthetic Everyday Card' })).toBeVisible();
  await expect(page.getByText('Account status: Open')).toBeVisible();
  await expect(page.getByText('£10,000.00')).toBeVisible();
  await expect(page.getByText('**** 4821')).toBeVisible();
  await expect(page.getByText('freshness unavailable')).toBeVisible();

  // Balance breakdown
  await page.getByRole('link', { name: 'View dated balance breakdown' }).click();
  await expect(page.getByRole('heading', { name: 'Dated balance breakdown', level: 1 })).toBeVisible();
  await expect(page.getByText('24 Nov 2026, 08:15 UTC')).toBeVisible();
  await expect(page.getByText('£4,862.35')).toBeVisible();
  await expect(page.getByText('Pending total', { exact: true })).toBeVisible();
  const ranks = page.getByRole('list', { name: 'Balance categories in source rank order' }).getByRole('heading', { level: 3 });
  await expect(ranks).toHaveCount(5);
  await expect(ranks.first()).toHaveText('Standard purchases');

  // Transactions
  await page.getByRole('link', { name: 'Transactions' }).first().click();
  const transactions = page.getByRole('table', { name: 'Account transactions' });
  await expect(transactions).toBeVisible();
  await expect(transactions.getByText('Status: Pending').first()).toBeVisible();
  await expect(transactions.getByText('Status: Posted').first()).toBeVisible();
  await expect(transactions.getByText('**** 4821').first()).toBeVisible();

  // Payments (information only)
  await page.getByRole('link', { name: 'Payments' }).first().click();
  const payments = page.getByRole('table', { name: 'Payment history' });
  await expect(payments).toBeVisible();
  await expect(payments.getByText('PMT-1', { exact: true })).toBeVisible();
  await expect(payments.getByText('Status: Completed').first()).toBeVisible();
  await expect(payments.getByText('****1234').first()).toBeVisible();
  await expect(page.getByRole('button', { name: /make|schedule|cancel|amend/i })).toHaveCount(0);
});
