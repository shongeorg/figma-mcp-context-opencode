import { defineConfig, devices } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:8000";

export default defineConfig({
  testDir: "./tests",

  timeout: 30 * 1000,

  expect: {
    timeout: 5000,
  },

  fullyParallel: true,

  retries: 1,

  workers: 2,

  forbidOnly: !!process.env.CI,

  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],

  use: {
    baseURL: BASE_URL,

    reducedMotion: "reduce",

    trace: "on-first-retry",

    video: "on-first-retry",

    screenshot: "only-on-failure",

    actionTimeout: 25 * 1000,

    navigationTimeout: 30 * 1000,
  },

  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: ["--enable-features=NetworkService,Preconnect"],
        },
      },
    },

    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },

    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },

    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "Mobile Safari",
      use: { ...devices["iPhone 12"] },
    },
  ],

});
