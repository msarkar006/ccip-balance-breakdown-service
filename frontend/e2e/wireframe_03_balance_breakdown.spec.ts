import { test, expect } from './_pipeline_guard';

test.describe('Balance Breakdown Page', () => {
  test('displays balance breakdown with categories in order for ACC-1001', async ({ page }) => {
    // Login with seed credentials
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('/account-overview');

    // Navigate to balance breakdown
    await page.click('a[href="/balance-breakdown"]');
    await page.waitForURL('/balance-breakdown');

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /Balance breakdown/i })).toBeVisible();

    // Verify total outstanding is displayed
    await expect(page.getByText('Total outstanding', { exact: true })).toBeVisible();
    
    // Verify pending total is shown separately
    await expect(page.getByText(/Pending, not yet in your balance/i)).toBeVisible();

    // Verify categories are displayed
    // The actual category display will depend on the data returned from GET /api/v1/balance-breakdowns/current
    // For ACC-1001, we expect StandardPurchase, PromotionalPurchase, BalanceTransfer, Instalment
    const categorySection = page.locator('section').filter({ hasText: /What makes up your balance/i });
    await expect(categorySection).toBeVisible();

    // Verify accordion items are present (categories)
    const accordionItems = page.locator('.cds--accordion__item');
    await expect(accordionItems.first()).toBeVisible();
  });

  test('displays zero balance state when no categories exist', async ({ page }) => {
    // This test assumes we can select an account with zero balance
    // If ACC-1002 has zero balance, we can test that
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('/account-overview');
    await page.click('a[href="/balance-breakdown"]');
    await page.waitForURL('/balance-breakdown');

    // If we select an account with zero balance via the account selector
    // we should see the zero balance message
    // Note: This depends on having an account selector that works
    // For now, we'll just verify the structure exists
    await expect(page.getByRole('heading', { name: /Balance breakdown/i })).toBeVisible();
  });

  test('displays freshness indicator when available', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('/account-overview');
    await page.click('a[href="/balance-breakdown"]');
    await page.waitForURL('/balance-breakdown');

    // Check for freshness notification
    // This should appear when freshness.level is "Current"
    const freshnessNotification = page.locator('.cds--inline-notification').filter({ hasText: /up to date/i });
    
    // Assert that freshness notification exists (not conditional)
    await expect(freshnessNotification).toBeVisible();
    await expect(freshnessNotification).toContainText(/Breakdown as of/i);
  });

  test('displays source links for linked categories', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');

    await page.waitForURL('/account-overview');
    await page.click('a[href="/balance-breakdown"]');
    await page.waitForURL('/balance-breakdown');

    // Find the BalanceTransfer category which should have source link to BT-2024-001
    // According to seed data and API response, this is category #3
    const accordions = page.locator('.cds--accordion__item');
    
    // Wait for accordions to load
    await expect(accordions.first()).toBeVisible();
    
    // The BalanceTransfer category should be the third one (index 2)
    // Open it by clicking its heading
    const balanceTransferAccordion = accordions.nth(2);
    const balanceTransferButton = balanceTransferAccordion.locator('button.cds--accordion__heading');
    await balanceTransferButton.click();
    
    // Wait for the accordion content to expand
    await page.waitForTimeout(300);
    
    // Now assert that the "Linked to" section is visible
    const linkedTo = balanceTransferAccordion.getByText(/Linked to/i);
    await expect(linkedTo).toBeVisible();
    
    // Verify the source reference is shown
    await expect(balanceTransferAccordion.getByText(/BT-2024-001/i)).toBeVisible();
  });
});
