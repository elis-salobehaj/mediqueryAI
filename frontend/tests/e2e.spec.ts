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
  await expect(page.getByPlaceholder(/ENTER INSTRUCTION/i)).toBeVisible({ timeout: 10000 });
});

test('shows error message on failed guest login', async ({ page }) => {
  // Mock failure route just for this test if needed, but for now we just want to see if real login fails
  // This test block is just a placeholder to remind us to check for [ ALERT: ... ]
});

test('E2E Test 1: Single-agent + Fast mode - list patients by state', async ({ page }) => {
  await page.goto('/');
  
  // Login as guest
  await page.getByRole('button', { name: /INITIATE GUEST PROTOCOL/i }).click();
  await expect(page.getByPlaceholder(/ENTER INSTRUCTION/i)).toBeVisible({ timeout: 10000 });
  
  // Ensure single-agent mode (multi-agent toggle OFF)
  const multiAgentToggle = page.locator('input[type="checkbox"]').first();
  if (await multiAgentToggle.isChecked()) {
    await multiAgentToggle.click();
  }
  
  // Ensure fast mode (thinking mode toggle OFF)
  const thinkingModeToggle = page.locator('input[type="checkbox"]').nth(1);
  if (await thinkingModeToggle.isChecked()) {
    await thinkingModeToggle.click();
  }
  
  // Send query
  const input = page.getByPlaceholder(/ENTER INSTRUCTION/i);
  await input.fill('list patients by state');
  await input.press('Enter');
  
  // Wait for response (up to 30s for LLM)
  await page.waitForTimeout(2000);
  
  // Verify SQL is generated
  const sqlText = await page.locator('text=/SELECT/i').first().textContent({ timeout: 30000 });
  expect(sqlText).toContain('SELECT');
  expect(sqlText?.toLowerCase()).toContain('from');
  expect(sqlText?.toLowerCase()).toContain('patient');
  
  // Verify no error messages
  const errorAlert = page.locator('text=/ERROR|ALERT.*ERROR/i');
  await expect(errorAlert).not.toBeVisible();
  
  // Verify data table appears
  await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
  
  // Verify table has headers and rows
  const headers = page.locator('thead th');
  await expect(headers.first()).toBeVisible();
  const rows = page.locator('tbody tr');
  await expect(rows.first()).toBeVisible();
  
  // Verify visualization appears
  await expect(page.locator('.plotly')).toBeVisible({ timeout: 5000 });
});

test('E2E Test 2: Single-agent + Thinking mode - list patients by state', async ({ page }) => {
  await page.goto('/');
  
  // Login as guest
  await page.getByRole('button', { name: /INITIATE GUEST PROTOCOL/i }).click();
  await expect(page.getByPlaceholder(/ENTER INSTRUCTION/i)).toBeVisible({ timeout: 10000 });
  
  // Ensure single-agent mode (multi-agent toggle OFF)
  const multiAgentToggle = page.locator('input[type="checkbox"]').first();
  if (await multiAgentToggle.isChecked()) {
    await multiAgentToggle.click();
  }
  
  // Enable thinking mode
  const thinkingModeToggle = page.locator('input[type="checkbox"]').nth(1);
  if (!await thinkingModeToggle.isChecked()) {
    await thinkingModeToggle.click();
  }
  
  // Send query
  const input = page.getByPlaceholder(/ENTER INSTRUCTION/i);
  await input.fill('list patients by state');
  await input.press('Enter');
  
  // Wait for response
  await page.waitForTimeout(2000);
  
  // Verify SQL is generated
  const sqlText = await page.locator('text=/SELECT/i').first().textContent({ timeout: 30000 });
  expect(sqlText).toContain('SELECT');
  expect(sqlText?.toLowerCase()).toContain('from');
  expect(sqlText?.toLowerCase()).toContain('patient');
  
  // Verify thinking process is shown
  const thinkingText = page.locator('text=/Analyzing|Generating|Processing/i');
  await expect(thinkingText.first()).toBeVisible({ timeout: 5000 });
  
  // Verify no error messages
  const errorAlert = page.locator('text=/ERROR|ALERT.*ERROR/i');
  await expect(errorAlert).not.toBeVisible();
  
  // Verify data table appears
  await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
  const headers = page.locator('thead th');
  await expect(headers.first()).toBeVisible();
  const rows = page.locator('tbody tr');
  await expect(rows.first()).toBeVisible();
  
  // Verify visualization appears
  await expect(page.locator('.plotly')).toBeVisible({ timeout: 5000 });
});

test('E2E Test 3: Multi-agent + Fast mode - list patients by state', async ({ page }) => {
  await page.goto('/');
  
  // Login as guest
  await page.getByRole('button', { name: /INITIATE GUEST PROTOCOL/i }).click();
  await expect(page.getByPlaceholder(/ENTER INSTRUCTION/i)).toBeVisible({ timeout: 10000 });
  
  // Enable multi-agent mode
  const multiAgentToggle = page.locator('input[type="checkbox"]').first();
  if (!await multiAgentToggle.isChecked()) {
    await multiAgentToggle.click();
  }
  
  // Ensure fast mode (thinking mode toggle OFF)
  const thinkingModeToggle = page.locator('input[type="checkbox"]').nth(1);
  if (await thinkingModeToggle.isChecked()) {
    await thinkingModeToggle.click();
  }
  
  // Send query
  const input = page.getByPlaceholder(/ENTER INSTRUCTION/i);
  await input.fill('list patients by state');
  await input.press('Enter');
  
  // Wait for response
  await page.waitForTimeout(2000);
  
  // Verify SQL is generated
  const sqlText = await page.locator('text=/SELECT/i').first().textContent({ timeout: 45000 });
  expect(sqlText).toContain('SELECT');
  expect(sqlText?.toLowerCase()).toContain('from');
  expect(sqlText?.toLowerCase()).toContain('patient');
  
  // Verify no error messages
  const errorAlert = page.locator('text=/ERROR|ALERT.*ERROR/i');
  await expect(errorAlert).not.toBeVisible();
  
  // Verify data table appears
  await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
  const headers = page.locator('thead th');
  await expect(headers.first()).toBeVisible();
  const rows = page.locator('tbody tr');
  await expect(rows.first()).toBeVisible();
  
  // Verify visualization appears
  await expect(page.locator('.plotly')).toBeVisible({ timeout: 5000 });
});

test('E2E Test 4: Multi-agent + Thinking mode - list patients by state', async ({ page }) => {
  await page.goto('/');
  
  // Login as guest
  await page.getByRole('button', { name: /INITIATE GUEST PROTOCOL/i }).click();
  await expect(page.getByPlaceholder(/ENTER INSTRUCTION/i)).toBeVisible({ timeout: 10000 });
  
  // Enable multi-agent mode
  const multiAgentToggle = page.locator('input[type="checkbox"]').first();
  if (!await multiAgentToggle.isChecked()) {
    await multiAgentToggle.click();
  }
  
  // Enable thinking mode
  const thinkingModeToggle = page.locator('input[type="checkbox"]').nth(1);
  if (!await thinkingModeToggle.isChecked()) {
    await thinkingModeToggle.click();
  }
  
  // Send query
  const input = page.getByPlaceholder(/ENTER INSTRUCTION/i);
  await input.fill('list patients by state');
  await input.press('Enter');
  
  // Wait for response
  await page.waitForTimeout(2000);
  
  // Verify SQL is generated
  const sqlText = await page.locator('text=/SELECT/i').first().textContent({ timeout: 45000 });
  expect(sqlText).toContain('SELECT');
  expect(sqlText?.toLowerCase()).toContain('from');
  expect(sqlText?.toLowerCase()).toContain('patient');
  
  // Verify multi-agent thoughts are shown with numbered steps
  const agentThoughts = page.locator('text=/\\[\\d+\\]|Schema Navigator|SQL Writer|Critic/i');
  await expect(agentThoughts.first()).toBeVisible({ timeout: 5000 });
  
  // Verify no error messages
  const errorAlert = page.locator('text=/ERROR|ALERT.*ERROR/i');
  await expect(errorAlert).not.toBeVisible();
  
  // Verify data table appears
  await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
  const headers = page.locator('thead th');
  await expect(headers.first()).toBeVisible();
  const rows = page.locator('tbody tr');
  await expect(rows.first()).toBeVisible();
  
  // Verify visualization appears
  await expect(page.locator('.plotly')).toBeVisible({ timeout: 5000 });
});
