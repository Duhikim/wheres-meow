import { expect, type Browser, type Page } from "@playwright/test";

/** 이번 실행에서 겹치지 않는 짧은 꼬리표. 닉네임은 12자 제한이 있다. */
export const stamp = () => Date.now().toString(36).slice(-4);

/** 새 브라우저 문맥 하나(쿠키·저장소가 분리된 사람 한 명). 콘솔 오류를 모은다. */
export async function newPlayer(browser: Browser): Promise<{ page: Page; errors: string[] }> {
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error" && !m.text().includes("favicon") && !m.text().includes("401")) errors.push(m.text());
  });
  return { page, errors };
}

export async function enterAsGuest(page: Page, nickname: string, path = "/"): Promise<void> {
  await page.goto(path);
  await page.fill("#nickname", nickname);
  await page.getByRole("button", { name: "게스트로 시작" }).click();
}

export async function isMyTurn(page: Page): Promise<boolean> {
  return ((await page.locator(".turn-label").textContent()) ?? "").includes("내 차례");
}

/**
 * 차례인 쪽이 닫힌 칸 하나를 열고, 서버 응답으로 판이 바뀔 때까지 기다린다.
 * 직전 수의 결과가 두 화면에 모두 도착해 정확히 한쪽만 "내 차례"가 될 때까지 먼저 기다린다.
 */
export async function playOneMove(a: Page, b: Page): Promise<void> {
  const closedCount = (p: Page) => p.locator(".cell.closed").count();
  await expect
    .poll(
      async () =>
        (await gameOver(a, b)) ||
        ((await isMyTurn(a)) !== (await isMyTurn(b)) && (await closedCount(a)) === (await closedCount(b))),
    )
    .toBe(true);
  if (await gameOver(a, b)) return;
  const mover = (await isMyTurn(a)) ? a : b;
  const closed = mover.locator(".cell.closed:not(.pending)");
  const before = await closed.count();
  await closed.first().click();
  await expect.poll(async () => (await mover.locator(".result-card").count()) > 0 || (await closed.count()) < before).toBe(true);
}

/** 어느 한쪽 화면에라도 결과 카드가 떴다. */
export async function gameOver(a: Page, b: Page): Promise<boolean> {
  return (await a.locator(".result-card").count()) + (await b.locator(".result-card").count()) > 0;
}

export async function forfeit(page: Page): Promise<void> {
  await page.getByRole("button", { name: "기권", exact: true }).click();
  await page.getByRole("button", { name: "기권 확정" }).click();
}

export async function startQuickMatch(a: Page, b: Page): Promise<void> {
  await a.getByRole("button", { name: /빠른 대전/ }).click();
  await expect(a.getByText("상대를 찾는 중")).toBeVisible();
  await b.getByRole("button", { name: /빠른 대전/ }).click();
  await a.waitForURL(/\/play\//);
  await b.waitForURL(/\/play\//);
}
