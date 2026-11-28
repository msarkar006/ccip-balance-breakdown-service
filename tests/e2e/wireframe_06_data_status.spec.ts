import { expect, test } from './_pipeline_guard';

test('wireframe_06: Data status opens from the side navigation with no /api request', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Account overview', level: 1 })).toBeVisible();

  // Let the overview finish its own loading so only the Data status page's traffic is counted.
  await expect(page.getByText('ACC-1001').first()).toBeVisible();
  await page.waitForLoadState('networkidle');

  const apiCalls: string[] = [];
  page.on('request', (request) => {
    if (new URL(request.url()).pathname.startsWith('/api')) apiCalls.push(request.url());
  });

  await page.getByRole('navigation', { name: 'Side navigation' }).getByRole('link', { name: 'Data status and limitations' }).click();
  await expect(page.getByRole('heading', { name: 'Data status and limitations', level: 1 })).toBeVisible();
  const table = page.getByRole('table', { name: 'Freshness labels and what they mean' });
  for (const label of ['freshness unavailable', 'unconfirmed freshness', 'stale']) {
    await expect(table.getByText(label, { exact: true })).toBeVisible();
  }
  expect(apiCalls).toEqual([]);
});
