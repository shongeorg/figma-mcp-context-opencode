import { defineConfig, devices } from "@playwright/test";

/**
 * 📍 BASE URL — прописується тут в одному місці
 * Змініть це значення для тестування іншого сайту
 */
const BASE_URL = "http://localhost:3333";

export default defineConfig({
  testDir: "./tests",

  // Повна назва тесту має виконуватися за цей час
  timeout: 30 * 1000,

  // Час очікування для expect.assertions()
  expect: {
    timeout: 5000,
  },

  // Запускати тести паралельно
  fullyParallel: true,

  // Кількість повторних спроб при невдачі
  retries: 1,

  // Кількість воркерів (паралельних процесів)
  // NOTE: 2 (not default = CPU count): Mobile Safari fullPage captures are
  // CPU-rasterized (~119MP desktop / ~33MP mobile) and 4 concurrent workers
  // on this 4-core box blew 25s screenshot budgets; 2 workers halves
  // contention with only a modest increase in total run time.
  workers: 2,

  // Чи запускати тести, які залишилися після попереднього запуску
  forbidOnly: !!process.env.CI,

  // Сторонні звіти
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],

  // Спільні налаштування для всіх тестів
  use: {
    /**
     * 📍 BASE URL — використовується всіма тестами
     * Всі відносні URL в тестах будуть відноситися до цього базового
     */
    baseURL: BASE_URL,

    // Збирати trace при кожній невдачі
    trace: "on-first-retry",

    // Збирати відео при кожній невдачі
    video: "on-first-retry",

    // Скріншоти при невдачах
    screenshot: "only-on-failure",

    // Actionability checks
    // NOTE: 25s (not default 10s) — Mobile Safari fullPage capture at
    // deviceScaleFactor=3 (~119MP at the current ~6900px page height) is
    // CPU-rasterized and this machine has only 4 cores; 14s was flaking
    // under parallel test load (measured ~13.9s solo).
    actionTimeout: 25 * 1000,

    // Навігація таймаут
    navigationTimeout: 30 * 1000,
  },

  // Конфігурація проектів для різних браузерів
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

    // Мобільні пристрої
    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "Mobile Safari",
      use: { ...devices["iPhone 12"] },
    },
  ],

  // Запуск локального дев-сервера перед тестами
  // webServer: {
  //   command: 'npm run dev',
  //   port: 3333,
  //   timeout: 120 * 1000,
  //   reuseExistingServer: !process.env.CI,
  // },
});
