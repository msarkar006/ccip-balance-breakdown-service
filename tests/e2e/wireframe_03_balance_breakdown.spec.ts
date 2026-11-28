import { expect, test } from './_pipeline_guard';

test('customer reads the dated balance breakdown reached from the account overview', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'View dated balance breakdown' }).click();

  await expect(page.getByRole('heading', { name: 'Dated balance breakdown', level: 1 })).toBeVisible();
  await expect(page.getByText('unconfirmed freshness')).toBeVisible();
  await expect(page.getByText('24 Nov 2026, 08:15 UTC')).toBeVisible();
  await expect(page.getByText('£4,862.35')).toBeVisible();
  await expect(page.getByText('£114.20')).toBeVisible();
  await expect(page.getByText('Pending total', { exact: true })).toBeVisible();
  const ranks = page.getByRole('list', { name: 'Balance categories in source rank order' }).getByRole('heading', { level: 3 });
  await expect(ranks).toHaveCount(5);
  await expect(ranks.first()).toHaveText('Standard purchases');
  await expect(page.getByText('BT-1')).toBeVisible();
  await expect(page.getByText('IP-66', { exact: true })).toBeVisible();
});
