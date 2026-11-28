import { expect, test } from './_pipeline_guard';

test('wireframe_01: bad login is refused, then a good login lands on the account overview', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'Sign in', level: 1 })).toBeVisible();

  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('Enter your username.')).toBeVisible();
  await expect(page.getByText('Enter your password.')).toBeVisible();

  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('not-the-password');
  await page.getByRole('button', { name: 'Show' }).click();
  await expect(page.getByLabel('Password', { exact: true })).toHaveAttribute('type', 'text');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('Sign-in failed')).toBeVisible();
  await expect(page).toHaveURL(/\/login/);

  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Account overview', level: 1 })).toBeVisible();
  await expect(page.getByText('ACC-1001').first()).toBeVisible();
});
