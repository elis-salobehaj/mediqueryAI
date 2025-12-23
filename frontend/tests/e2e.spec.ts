import { test, expect } from '@playwright/test';

test('homepage has title and main elements', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/MediQuery AI/);

  // Expect current login button text "AUTHENTICATE"
  await expect(page.getByRole('button', { name: /AUTHENTICATE/i })).toBeVisible();

  // Test Guest Login Flow
  await page.getByRole('button', { name: /INITIATE GUEST PROTOCOL/i }).click();

  // Expect to see the ChatBox input after login
  // Wait up to 10s for backend response
  await expect(page.getByPlaceholder(/Enter your medical query/i)).toBeVisible({ timeout: 10000 });
});

test('shows error message on failed guest login', async ({ page }) => {
  // Mock failure route just for this test if needed, but for now we just want to see if real login fails
  // This test block is just a placeholder to remind us to check for [ ALERT: ... ]
});
