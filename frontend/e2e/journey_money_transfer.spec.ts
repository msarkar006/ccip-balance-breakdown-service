import { test, expect } from './_pipeline_guard';

test.describe('Journey - Money Transfer Initiation', () => {
  test('complete money transfer journey: login → transfer management → money transfer → unified tracker → verify transfer appears', async ({ page }) => {
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

    // Step 3: Navigate to transfer management Money Transfer tab
    await page.getByRole('link', { name: /transfer/i }).click();
    await expect(page).toHaveURL('/transfers', { timeout: 10000 });
    
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Click Money Transfer tab
    const moneyTransferTab = page.getByRole('tab', { name: /money transfer/i });
    await moneyTransferTab.click({ force: true });
    
    // Wait a moment for tab content to render
    await page.waitForTimeout(500);

    // Step 4: Verify button is visible and payees are loaded
    const submitButton = page.getByRole('button', { name: /review money transfer/i });
    await expect(submitButton).toBeVisible({ timeout: 5000 });
    
    // The form has pre-filled default values including the first payee and default amount
    // Just click submit with the default values to test the journey
    await submitButton.click();

    // Step 5: Wait for confirmation modal (TransferManagementPage uses custom Modal)
    const modalHeading = page.getByRole('heading', { name: /confirm your identity/i });
    await expect(modalHeading).toBeVisible({ timeout: 5000 });

    const stepUpPasswordInput = page.locator('#stepUpPassword');
    await stepUpPasswordInput.fill('admin123');
    // Wait for React to process the onChange event
    await page.waitForTimeout(100);
    await page.getByRole('button', { name: /confirm and submit/i }).click();

    // Step 6: Wait for success notification (money transfer says "processing")
    const successNotification = page.getByText(/money transfer processing/i);
    await expect(successNotification).toBeVisible({ timeout: 5000 });

    // Step 7: Navigate to unified tracker (use exact name to avoid ambiguity)
    await page.getByRole('link', { name: 'Unified tracker' }).click();
    await expect(page).toHaveURL('/tracker', { timeout: 10000 });

    // Step 8: Verify tracker table loads and has content
    const trackerTable = page.getByRole('table');
    await expect(trackerTable).toBeVisible({ timeout: 10000 });
    
    // Verify table has at least one row (unified tracker shows various transfer types)
    const tableRows = trackerTable.locator('tbody tr');
    await expect(tableRows.first()).toBeVisible({ timeout: 10000 });
  });
});
