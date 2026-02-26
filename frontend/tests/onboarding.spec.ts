import { test, expect } from "@playwright/test";

test.describe("Onboarding flow", () => {
  const TEST_EMAIL = `test-${Date.now()}@example.com`;
  const TEST_PASSWORD = "password123";
  const TEST_AGENCY = "Test Agency";

  test("register -> add site -> verify flow", async ({ page }) => {
    // 1. Navigate to register page
    await page.goto("/auth/register");
    await expect(page.locator("h1")).toContainText("Create Account");

    // 2. Fill and submit registration form
    await page.fill("#agency-name", TEST_AGENCY);
    await page.fill("#email", TEST_EMAIL);
    await page.fill("#password", TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // 3. Should redirect to onboarding / add-site
    await page.waitForURL("**/onboarding/add-site", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Add Your Site");

    // 4. Fill and submit add-site form
    await page.fill("#domain", "example.com");
    await page.fill("#site-name", "My Test Site");
    await page.click('button[type="submit"]');

    // 5. Should proceed to Google step
    await page.waitForURL("**/onboarding/google", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Connect Google Ads");

    // 6. Skip Google step
    await page.click("text=Skip for now");
    await page.waitForURL("**/onboarding/meta", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Connect Meta Ads");

    // 7. Skip Meta step
    await page.click("text=Skip for now");
    await page.waitForURL("**/onboarding/slack", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Install Slack Bot");

    // 8. Skip Slack step
    await page.click("text=Skip for now");
    await page.waitForURL("**/onboarding/verify", { timeout: 10_000 });
    await expect(page.locator("h2")).toContainText("Install Tracking Pixel");

    // 9. Pixel snippet should be visible
    await expect(page.locator("pre")).toBeVisible();

    // 10. Finish setup
    await page.click("text=Finish Setup");
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
