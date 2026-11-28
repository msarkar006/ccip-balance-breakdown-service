import { expect, test } from './_pipeline_guard';

test('customer signs in through the form and lands on data from the backend', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Sign in', level: 1 })).toBeVisible();

  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();

  await expect(page.getByRole('heading', { name: 'Account overview', level: 1 })).toBeVisible();
  await expect(page.getByText('Read-only prototype using synthetic data')).toBeVisible();
  // Both values below come from the backend: the login response and the seeded account.
  await expect(page.getByRole('img', { name: 'Signed in as synthetic.customer01' })).toBeVisible();
  await expect(page.getByText('ACC-1001').first()).toBeVisible();
});
