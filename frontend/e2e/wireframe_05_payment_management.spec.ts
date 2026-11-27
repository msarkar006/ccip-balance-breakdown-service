import { test, expect } from './_pipeline_guard';

test.describe('Payment Management (Wireframe 05)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/account-overview');
  });

  test('displays payment guidance and form', async ({ page }) => {
    await page.goto('/payments');
    
    await expect(page.locator('h1')).toContainText('Payment Management');
    await expect(page.getByText('Make a payment')).toBeVisible();
    await expect(page.getByText(/Minimum payment/).first()).toBeVisible();
    await expect(page.getByText(/Due by/)).toBeVisible();
    await expect(page.getByText(/Current balance/).first()).toBeVisible();
  });

  test('displays direct debit coverage information', async ({ page }) => {
    await page.goto('/payments');
    
    await expect(page.getByText(/Direct debit/i)).toBeVisible();
  });

  test('submits payment with step-up authentication', async ({ page }) => {
    await page.goto('/payments');
    
    await page.click('label[for="amount-minimum"]');
    await page.click('button:has-text("Review payment")');
    
    // Wait for the visible modal dialog (not just any heading)
    const modal = page.locator('[role="dialog"][aria-label="Verify your identity"]').first();
    await expect(modal).toBeVisible();
    
    await modal.locator('#step-up-password').fill('admin123');
    await modal.getByRole('button', { name: /verify and continue/i }).click();
    
    await expect(page.getByText(/Payment submitted/)).toBeVisible();
  });

  test('displays payment history with status tags', async ({ page }) => {
    await page.goto('/payments');
    
    await expect(page.getByText('Payment history')).toBeVisible();
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    await expect(table.getByText('Date')).toBeVisible();
    await expect(table.getByText('Type')).toBeVisible();
    await expect(table.getByText('Method')).toBeVisible();
    await expect(table.getByText('Amount')).toBeVisible();
    await expect(table.getByText('Status')).toBeVisible();
  });
});
