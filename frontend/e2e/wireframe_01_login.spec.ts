import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 01 - Login', () => {
  test('logs in through login form with seed credentials and redirects to account overview', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Verify we're on the login page - try multiple heading levels
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible({ timeout: 10000 });

    // Fill in login form with seed credentials
    const usernameInput = page.locator('#username');
    const passwordInput = page.locator('#password');
    
    await usernameInput.clear();
    await usernameInput.fill('admin@example.com');
    await passwordInput.clear();
    await passwordInput.fill('admin123');

    // Submit the form
    await page.getByRole('button', { name: /log in/i }).click();

    // Wait for redirect to account overview
    await expect(page).toHaveURL('/account-overview', { timeout: 10000 });

    // Verify we're on the account overview page
    await expect(page.locator('h1')).toContainText(/account overview/i, { timeout: 10000 });
  });

  test('shows error message with invalid credentials', async ({ page, apiGuard }) => {
    // Allow 401 for wrong credentials and 429 for rate limiting - both are expected
    apiGuard.allow(401, '/api/v1/auth/login');
    apiGuard.allow(429, '/api/v1/auth/login');
    
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Clear default values and enter wrong credentials
    const usernameInput = page.locator('#username');
    const passwordInput = page.locator('#password');
    
    await usernameInput.clear();
    await usernameInput.fill('wrong@example.com');
    await passwordInput.clear();
    await passwordInput.fill('wrongpassword');

    // Submit the form
    await page.getByRole('button', { name: /log in/i }).click();

    // Wait a moment for the error to appear
    await page.waitForTimeout(500);

    // Verify error notification appears (use first() as both title and subtitle contain this text)
    await expect(page.getByRole('status').getByText(/we could not log you in/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('shows validation errors when fields are empty', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Clear default values
    const usernameInput = page.locator('#username');
    const passwordInput = page.locator('#password');
    
    await usernameInput.clear();
    await passwordInput.clear();

    // Submit the form
    await page.getByRole('button', { name: /log in/i }).click();

    // Verify validation errors appear in the form requirement divs
    await expect(page.locator('#username-error-msg')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#username-error-msg')).toHaveText('Enter your username');
    await expect(page.locator('#password-error-msg')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#password-error-msg')).toHaveText('Enter your password');
  });
});
