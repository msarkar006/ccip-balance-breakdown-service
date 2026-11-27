import { test, expect } from './_pipeline_guard';

test.describe('Rewards and Offers (Wireframe 08)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/account-overview');
  });

  test('displays rewards programme summary and offers for ACC-1001', async ({ page }) => {
    await page.goto('/rewards');
    
    await expect(page.getByRole('heading', { name: 'Rewards and offers' })).toBeVisible();
    
    const accountSelect = page.locator('#accountSelect');
    await accountSelect.selectOption('ACC-1001');
    
    const programmeName = page.getByText(/rewards plus/i);
    await expect(programmeName).toBeVisible();
    
    const pointsBalance = page.getByText(/1,250 points/i);
    await expect(pointsBalance).toBeVisible();
    
    const statusTag = page.getByText('Active');
    await expect(statusTag).toBeVisible();
    
    const offersHeading = page.getByRole('heading', { name: /offers for this account/i });
    await expect(offersHeading).toBeVisible();
  });

  test('displays empty state for ACC-1002', async ({ page }) => {
    await page.goto('/rewards');
    
    const accountSelect = page.locator('#accountSelect');
    await accountSelect.selectOption('ACC-1002');
    
    const emptyStateHeading = page.getByRole('heading', { name: /nothing to show for this account right now/i });
    await expect(emptyStateHeading).toBeVisible();
    
    const emptyStateMessage = page.getByText(/no rewards programme and no offers available/i);
    await expect(emptyStateMessage).toBeVisible();
  });

  test('displays offer cards with details', async ({ page }) => {
    await page.goto('/rewards');
    
    const accountSelect = page.locator('#accountSelect');
    await accountSelect.selectOption('ACC-1001');
    
    const offerCards = page.locator('.cds--tile');
    await expect(offerCards.first()).toBeVisible();
  });

  test('allows navigation between accounts', async ({ page }) => {
    await page.goto('/rewards');
    
    const accountSelect = page.locator('#accountSelect');
    
    await accountSelect.selectOption('ACC-1001');
    await expect(page.getByText(/rewards plus/i)).toBeVisible();
    
    await accountSelect.selectOption('ACC-1002');
    await expect(page.getByText(/nothing to show/i)).toBeVisible();
  });
});
