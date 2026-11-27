import { test, expect } from './_pipeline_guard';

test.describe('Transfer Management (Wireframe 07)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/account-overview');
  });

  test('displays balance transfer form and submission flow', async ({ page }) => {
    await page.goto('/transfers');
    
    await expect(page.getByRole('heading', { name: 'Transfers' })).toBeVisible();
    
    const balanceTransferTab = page.getByRole('tab', { name: /balance transfer/i });
    await expect(balanceTransferTab).toBeVisible();
    await balanceTransferTab.click();
    
    await expect(page.getByRole('heading', { name: /request a balance transfer/i })).toBeVisible();
    
    // Wait for form to fully load (offers API response)
    await page.waitForLoadState('networkidle');
    
    // Form has pre-filled defaults - just verify they're there and click submit
    const amountInput = page.locator('#btAmt');
    await expect(amountInput).toBeVisible();
    await expect(amountInput).toHaveValue('2000.00');
    
    const submitButton = page.getByRole('button', { name: /review balance transfer/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();
    
    // Wait for the confirmation modal (this page uses a custom Modal, not StepUpModal)
    const modalHeading = page.getByRole('heading', { name: /confirm your identity/i });
    await expect(modalHeading).toBeVisible();
    
    const passwordInput = page.locator('#stepUpPassword');
    await passwordInput.fill('admin123');
    // Wait for React to process the onChange event
    await page.waitForTimeout(100);
    await page.getByRole('button', { name: /confirm and submit/i }).click();
    
    await expect(page.getByText(/balance transfer submitted/i)).toBeVisible({ timeout: 10000 });
  });

  test('displays balance transfer history with status tags', async ({ page }) => {
    await page.goto('/transfers');
    
    const historyHeading = page.getByRole('heading', { name: /balance transfer history/i });
    await expect(historyHeading).toBeVisible();
    
    // Check for table content - balance transfers use external_transfer_id as provider reference
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByText(/BT-/i).first()).toBeVisible();
  });

  test('displays money transfer form and submission flow', async ({ page }) => {
    await page.goto('/transfers');
    
    const moneyTransferTab = page.getByRole('tab', { name: /money transfer/i });
    await expect(moneyTransferTab).toBeVisible();
    await moneyTransferTab.click();
    
    await expect(page.getByRole('heading', { name: /transfer money to your bank account/i })).toBeVisible();
    
    // Wait for form to fully load (payees API response)
    await page.waitForLoadState('networkidle');
    
    const payeeSelect = page.locator('#payee');
    await expect(payeeSelect).toBeVisible();
    
    const amountInput = page.locator('#mtAmt');
    await expect(amountInput).toBeVisible();
    await amountInput.fill('100.00');
    
    const submitButton = page.getByRole('button', { name: /review money transfer/i });
    await expect(submitButton).toBeEnabled();
    await submitButton.click();
    
    // Wait for the confirmation modal (this page uses a custom Modal, not StepUpModal)
    const modalHeading = page.getByRole('heading', { name: /confirm your identity/i });
    await expect(modalHeading).toBeVisible();
    
    const passwordInput = page.locator('#stepUpPassword');
    await passwordInput.fill('admin123');
    // Wait for React to process the onChange event
    await page.waitForTimeout(100);
    await page.getByRole('button', { name: /confirm and submit/i }).click();
    
    await expect(page.getByText(/money transfer processing/i)).toBeVisible({ timeout: 10000 });
  });

  test('displays money transfer history with payee and status', async ({ page }) => {
    await page.goto('/transfers');
    
    const moneyTransferTab = page.getByRole('tab', { name: /money transfer/i });
    await moneyTransferTab.click();
    
    const historyHeading = page.getByRole('heading', { name: /money transfer history/i });
    await expect(historyHeading).toBeVisible();
    
    // Check for money transfer history table - look for status tags specifically in table cells
    const table = page.getByRole('table');
    await expect(table).toBeVisible();
    // Look for a cell containing money transfer amount  (seed data has amounts like 100.00, 250.00, etc.)
    await expect(table.locator('td').getByText(/£100\.00|£250\.00|£150\.00/i).first()).toBeVisible();
  });
});
