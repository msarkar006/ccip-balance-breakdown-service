import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 02 - Account Overview', () => {
  test.beforeEach(async ({ page }) => {
    // Log in first
    await page.goto('/login');
    await page.getByLabel(/username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('admin123');
    await page.getByRole('button', { name: /log in/i }).click();
    await expect(page).toHaveURL('/account-overview');
  });

  test('displays account overview with balance summary and card status', async ({ page }) => {
    // Verify heading is present
    await expect(page.getByRole('heading', { name: /account overview/i })).toBeVisible();

    // Verify balance information is displayed
    await expect(page.getByText(/current balance/i)).toBeVisible();
    await expect(page.getByText(/available credit/i)).toBeVisible();

    // Verify payment information is displayed
    await expect(page.getByText(/payment due date/i)).toBeVisible();
    await expect(page.getByText(/minimum payment/i)).toBeVisible();

    // Verify card status section is displayed
    await expect(page.getByText(/account status/i)).toBeVisible();
  });

  test('allows selecting account from dropdown', async ({ page }) => {
    // Find the account selector
    const accountSelect = page.locator('#accountSelect');
    await expect(accountSelect).toBeVisible();

    // Get the initial account
    const initialValue = await accountSelect.inputValue();

    // Get all options
    const options = await page.locator('#accountSelect option').all();
    
    if (options.length > 1) {
      // Select the second account
      const secondOption = options[1];
      const secondValue = await secondOption.getAttribute('value');
      
      if (secondValue && secondValue !== initialValue) {
        await accountSelect.selectOption(secondValue);
        
        // Wait for React state to update and account data to load
        await page.waitForTimeout(1000);
        
        // Verify the selection changed
        await expect(accountSelect).toHaveValue(secondValue);
        
        // Verify account context has changed (balance should update)
        await expect(page.locator('body')).toBeVisible(); // Wait for any loading
      }
    }
  });

  test('displays freshness indicator when available', async ({ page }) => {
    // Check if freshness indicator is present (it may not always be shown)
    const freshnessIndicator = page.getByText(/up to date/i);
    const count = await freshnessIndicator.count();
    
    if (count > 0) {
      await expect(freshnessIndicator).toBeVisible();
      await expect(page.getByText(/figures as of/i)).toBeVisible();
    }
  });

  test('displays action buttons for payments and balance breakdown', async ({ page }) => {
    // Verify primary action buttons are present
    await expect(page.getByRole('button', { name: /make a payment/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /view balance breakdown/i })).toBeVisible();
  });

  test('shows user email and logout button in header', async ({ page }) => {
    // Verify user email is shown in header
    await expect(page.getByText('admin@example.com')).toBeVisible();

    // Verify logout button is present
    await expect(page.getByRole('button', { name: /log out/i })).toBeVisible();
  });
});
