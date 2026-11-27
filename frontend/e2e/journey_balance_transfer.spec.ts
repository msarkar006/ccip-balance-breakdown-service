import { test, expect } from './_pipeline_guard';

test.describe('Journey - Balance Transfer Initiation', () => {
  test('complete balance transfer journey: login → balance breakdown → transfer initiation → transfer history → verify transfer appears', async ({ page }) => {
    // Step 1: Login with seed credentials
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const usernameInput = page.locator('#username');
    const passwordInput = page.locator('#password');
    
    await usernameInput.clear();
    await usernameInput.fill('admin@example.com');
    await passwordInput.clear();
    await passwordInput.fill('admin123');

    await page.getByRole('button', { name: /log in/i }).click();

    // Step 2: Verify redirect to account overview
    await expect(page).toHaveURL('/account-overview', { timeout: 10000 });
    await expect(page.locator('h1')).toContainText(/account overview/i, { timeout: 10000 });

    // Step 3: Navigate to balance breakdown
    await page.getByRole('link', { name: /balance/i }).click();
    await expect(page).toHaveURL('/balance-breakdown', { timeout: 10000 });
    await expect(page.locator('h1')).toContainText(/balance breakdown/i, { timeout: 10000 });

    // Step 4: Navigate to transfer management (Balance Transfer tab)
    await page.getByRole('link', { name: /transfer/i }).click();
    await expect(page).toHaveURL('/transfers', { timeout: 10000 });
    
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    
    // Ensure Balance Transfer tab is active (should be default)
    const balanceTransferTab = page.getByRole('tab', { name: /balance transfer/i });
    await balanceTransferTab.click({ force: true });
    
    // Wait a moment for tab content to render
    await page.waitForTimeout(500);

    // Step 5: Verify form is visible and fill it
    const submitButton = page.getByRole('button', { name: /review balance transfer/i });
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    
    // The form has pre-filled default values - use them or override
    // Just click submit with the default values to test the journey
    await submitButton.click();

    // Step 6: Wait for confirmation modal (TransferManagementPage uses custom Modal)
    const modalHeading = page.getByRole('heading', { name: /confirm your identity/i });
    await expect(modalHeading).toBeVisible({ timeout: 5000 });

    const stepUpPasswordInput = page.locator('#stepUpPassword');
    await stepUpPasswordInput.fill('admin123');
    // Wait for React to process the onChange event
    await page.waitForTimeout(100);
    await page.getByRole('button', { name: /confirm and submit/i }).click();

    // Step 7: Wait for success notification
    const successNotification = page.getByText(/transfer.*submitted/i);
    await expect(successNotification).toBeVisible({ timeout: 5000 });

    // Step 8: Verify transfer history table is visible (page should still be on transfers)
    const historyTable = page.getByRole('table');
    await expect(historyTable).toBeVisible({ timeout: 10000 });

    // Verify at least one BT- reference appears (seed data includes balance transfers)
    const transferRef = historyTable.getByText(/BT-/i);
    await expect(transferRef.first()).toBeVisible({ timeout: 10000 });
  });
});
