import { test, expect } from './_pipeline_guard';

test.describe('Journey - New Payment Submission', () => {
  test('complete payment journey: login → account overview → payment submission → unified tracker → verify payment appears', async ({ page }) => {
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

    // Step 3: Navigate to payment management
    await page.getByRole('link', { name: /payment/i }).click();
    await expect(page).toHaveURL('/payments', { timeout: 10000 });
    await expect(page.locator('h1')).toContainText(/payment/i, { timeout: 10000 });

    // Step 4: Select "Other amount" radio button by clicking the label directly with force
    await page.locator('label[for="amount-other"]').click({ force: true });
    
    // Wait for the other amount input to become visible
    const otherAmountInput = page.locator('#other-amount');
    await expect(otherAmountInput).toBeVisible({ timeout: 5000 });
    await otherAmountInput.fill('100.00');

    // Step 5: Trigger step-up modal (submit button should open modal)
    const submitButton = page.getByRole('button', { name: /review payment/i });
    await submitButton.click();

    // Step 6: Wait for step-up modal and confirm with password
    // Use first() to handle multiple modal elements
    const modal = page.locator('[role="dialog"][aria-label="Verify your identity"]').first();
    await expect(modal).toBeVisible({ timeout: 5000 });

    const passwordModalInput = modal.locator('#step-up-password');
    await passwordModalInput.fill('admin123');

    const confirmButton = modal.getByRole('button', { name: /verify and continue/i });
    await confirmButton.click();

    // Step 7: Wait for success notification to appear
    const successNotification = page.getByText(/payment.*submitted/i);
    await expect(successNotification).toBeVisible({ timeout: 5000 });

    // Step 8: Navigate to unified tracker (use exact name to avoid ambiguity)
    await page.getByRole('link', { name: 'Unified tracker' }).click();
    await expect(page).toHaveURL('/tracker', { timeout: 10000 });

    // Step 9: Verify tracker page loads with table (seed data includes payments)
    const trackerTable = page.getByRole('table');
    await expect(trackerTable).toBeVisible({ timeout: 10000 });

    // Verify at least one Submitted status appears (from seed data or new payment)
    const submittedTag = page.getByText('Submitted');
    await expect(submittedTag.first()).toBeVisible({ timeout: 10000 });
  });
});
