import { test, expect } from "@playwright/test";

test.describe("Onboarding flow", () => {
  const TEST_EMAIL = `test-${Date.now()}@example.com`;
  const TEST_PASSWORD = "password123";
  const TEST_INVITE = "epi-invite-test-code";

  test("register with site -> install pixel -> verify flow", async ({ page }) => {
    // 1. Navigate to register page
    await page.goto("/auth/register");
    await expect(page.locator("h1")).toContainText("Get Started with EPI");

    // 2. Fill and submit combined registration + site form
    await page.fill("#invite-code", TEST_INVITE);
    await page.fill("#email", TEST_EMAIL);
    await page.fill("#password", TEST_PASSWORD);
    await page.fill("#site-name", "My Test Site");
    await page.fill("#domain", "example.com");
    await page.click('button[type="submit"]');

    // 3. Should redirect straight to install-pixel
    await page.waitForURL("**/onboarding/install-pixel", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Install Tracking Pixel");

    // 4. Pixel snippet should be visible
    await expect(page.locator("pre")).toBeVisible();

    // 5. GTM tab should be available
    await page.click("text=Google Tag Manager");
    await expect(page.locator("pre")).toContainText("createElement");

    // 6. Skip to dashboard
    await page.click("text=Skip for now");
    await page.waitForURL("**/dashboard", { timeout: 10_000 });
    await expect(page.locator("h1")).toContainText("EPI Dashboard");
  });

  test("landing page redirects to login", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/auth/login", { timeout: 10_000 });
    await expect(page.locator("h1")).toContainText("Welcome Back");
  });

  test("login page has link to register", async ({ page }) => {
    await page.goto("/auth/login");
    const registerLink = page.locator('a[href="/auth/register"]');
    await expect(registerLink).toBeVisible();
    await expect(registerLink).toContainText("Register");
  });
});
