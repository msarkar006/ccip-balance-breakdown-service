import { expect, test, type Page } from './_pipeline_guard';

async function signIn(page: Page, username: string): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('customer submits a data rights request, sees it listed, then signs out', async ({ page }) => {
  await signIn(page, 'synthetic.customer01');
  await page.getByRole('link', { name: 'Your data rights' }).first().click();
  await expect(page.getByRole('heading', { name: 'Your data rights', level: 1 })).toBeVisible();
  await expect(page.getByText('Status: Received').first()).toBeVisible();
  const before = await page.getByText('Status: Received').count();

  await page.getByLabel('Request type').selectOption('export');
  await page.getByRole('button', { name: 'Submit request' }).click();
  await expect(page.getByText('Request received', { exact: true })).toBeVisible();
  await expect(page.getByText('Status: Received')).toHaveCount(before + 1);

  await page.getByRole('link', { name: 'Sign out' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto('/data-rights');
  await expect(page).toHaveURL(/\/login/);
});

test('administrator sees only data rights and the session ends on sign out', async ({ page }) => {
  await signIn(page, 'synthetic.admin01');
  await expect(page).toHaveURL(/\/data-rights$/);
  await expect(page.getByRole('heading', { name: 'Your data rights', level: 1 })).toBeVisible();
  await page.goto('/accounts');
  await expect(page).toHaveURL(/\/data-rights$/);

  await page.getByRole('link', { name: 'Sign out' }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goto('/data-rights');
  await expect(page).toHaveURL(/\/login/);
});
