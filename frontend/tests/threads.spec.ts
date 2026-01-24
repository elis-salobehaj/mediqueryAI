import { test, expect } from '@playwright/test';

test.describe('Thread Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('*/**/auth/token', async route => {
      await route.fulfill({ json: { access_token: 'mock-token', token_type: 'bearer' } });
    });

    await page.route('*/**/threads', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({ json: { threads: [] } });
      } else {
        await route.continue();
      }
    });

    await page.goto('http://localhost:3000');
    // Login flow if needed, or assume mock token stored (need to handle login UI if it appears)
    // Since we mock token in App.tsx typically or handling it via local storage

    // Fill login if redirected
    if (await page.getByPlaceholder('Username').isVisible()) {
      await page.getByPlaceholder('Username').fill('test');
      await page.getByPlaceholder('Password').fill('test');
      await page.getByRole('button', { name: 'Sign In' }).click();
    }
  });

  test('should create a new thread when sending a message', async ({ page }) => {
    // Mock the query response to return a new thread ID
    await page.route('*/**/query', async route => {
      await route.fulfill({
        json: {
          insight: 'Response',
          data: {},
          sql: '',
          meta: { thread_id: 'new-thread-id', thoughts: ['Thinking...'] }
        }
      });
    });

    await page.route('*/**/threads', async route => {
      await route.fulfill({ json: { threads: [{ id: 'new-thread-id', title: 'Test Query', updated_at: Date.now(), pinned: false }] } });
    });

    await page.getByPlaceholder('Ask a question...').fill('Test Query');
    await page.getByRole('button', { name: /send/i }).click();

    // Verification
    await expect(page.getByText('Test Query')).toBeVisible();
  });

  test('should rename a thread', async ({ page }) => {
    // Seed sidebar with a thread
    await page.route('*/**/threads', async route => {
      await route.fulfill({ json: { threads: [{ id: 't1', title: 'Original Name', updated_at: Date.now(), pinned: false }] } });
    });
    await page.reload();

    // Hover and click context menu
    await page.getByText('Original Name').hover();
    await page.locator('button').filter({ has: page.locator('svg') }).last().click(); // Simple heuristic for context menu button
    // A better selector would be based on the ThreadItem structure

    await page.getByText('Rename').click();
    await page.locator('input[value="Original Name"]').fill('Renamed Thread');
    await page.keyboard.press('Enter');

    // Verify UI update (optimistic or re-fetch)
    await expect(page.getByText('Renamed Thread')).toBeVisible();
  });
});
