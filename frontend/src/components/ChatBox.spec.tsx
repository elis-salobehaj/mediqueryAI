import { test, expect } from '@playwright/experimental-ct-react';
import ChatBox from './ChatBox';

test.use({ viewport: { width: 500, height: 500 } });

test('fetches and displays models from backend on mount', async ({ mount, page }) => {
  // Mock the API call
  await page.route('**/config/models', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 'test-model-1', name: 'Test Model 1' },
      ]),
    });
  });

  const component = await mount(<ChatBox messages={[]} setMessages={() => { }} />);

  // Expect the model to be displayed (Playwright locators are smart)
  await expect(component.getByText('Test Model 1')).toBeVisible();
});

test('handles fetch error by using fallback defaults', async ({ mount, page }) => {
  // Mock API failure
  await page.route('**/config/models', async route => {
    await route.abort();
  });

  const component = await mount(<ChatBox messages={[]} setMessages={() => { }} />);

  // Expect fallback default model (e.g., GEMMA 3 27B from your constants)
  // Note: Adjust text based on actual default in code
  await expect(component.getByText(/GEMMA 3 27B/i)).toBeVisible();
});
