import { defineConfig } from "@playwright/test";

// E2E_BASE 를 주면 이미 떠 있는 서버(예: 운영)를 상대하고, 없으면 start-server.sh 로 시험용 서버를 띄운다.
const external = process.env.E2E_BASE;
const port = process.env.E2E_PORT ?? "5100";

export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  fullyParallel: false, // 매칭 대기열을 공유하므로 한 번에 한 시나리오만 돌린다
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: external ?? `http://127.0.0.1:${port}`,
    // 설치된 Chrome 을 쓴다. CI 처럼 Chrome 이 없으면 E2E_CHANNEL= (빈 값)과 npx playwright install chromium 으로 바꾼다.
    channel: process.env.E2E_CHANNEL ?? "chrome",
    viewport: { width: 390, height: 844 },
    trace: "retain-on-failure",
  },
  webServer: external
    ? undefined
    : {
        command: "sh start-server.sh",
        url: `http://127.0.0.1:${port}/api/health`,
        timeout: 120_000,
        reuseExistingServer: false,
        stdout: "ignore", // 요청마다 찍히는 개발 서버 로그는 감춘다. 오류(stderr)는 그대로 보인다
      },
});
