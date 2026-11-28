import { expect, test } from './_pipeline_guard';

test('customer01 submits an export request and sees it listed as received', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.customer01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('link', { name: 'Your data rights' }).first().click();

  await expect(page.getByRole('heading', { name: 'Your data rights', level: 1 })).toBeVisible();
  await expect(page.getByText('Status: Received').first()).toBeVisible();
  const before = await page.getByText('Status: Received').count();

  await page.getByRole('button', { name: 'Submit request' }).click();
  await expect(page.getByText('Choose a request type.')).toBeVisible();

  await page.getByLabel('Request type').selectOption('deletion');
  await page.getByRole('button', { name: 'Submit request' }).click();

  await expect(page.getByText('Request received', { exact: true })).toBeVisible();
  await expect(page.getByText('Status: Received')).toHaveCount(before + 1);
  await expect(page.getByText('Deletion', { exact: true }).first()).toBeVisible();
});

test('administrator is sent to the data rights page only', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill('synthetic.admin01');
  await page.getByLabel('Password', { exact: true }).fill('Prototype!2026');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/data-rights$/);
  await expect(page.getByLabel('Subject reference')).toBeVisible();
  await page.goto('/accounts');
  await expect(page).toHaveURL(/\/data-rights$/);
});
