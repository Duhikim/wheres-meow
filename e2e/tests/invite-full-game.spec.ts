import { expect, test } from "@playwright/test";
import { enterAsGuest, gameOver, newPlayer, playOneMove, stamp } from "./support";

// 스펙 9.4: 브라우저 두 개가 초대 링크로 만나 25마리를 다 찾을 때까지 한 판을 둔다.
// 고양이 배치는 서버의 WHERESMEOW_TEST_SEED 로 고정되어 있다(start-server.sh). 운영 대상(E2E_BASE)에서는 건너뛴다.
test.skip(!!process.env.E2E_BASE, "끝까지 두는 대국은 시드를 고정한 시험 서버에서만 돌린다");

test("초대 링크로 들어와 고양이 25마리를 모두 찾을 때까지 한 판을 둔다", async ({ browser }) => {
  const tag = stamp();
  const host = await newPlayer(browser);
  const guest = await newPlayer(browser);
  const a = host.page;
  const b = guest.page;

  await enterAsGuest(a, `방장${tag}`);
  await a.getByRole("button", { name: "친구와 대결" }).click();
  const code = ((await a.locator(".room-code").textContent()) ?? "").trim();
  expect(code).toMatch(/^[A-Z0-9]{6}$/);

  await enterAsGuest(b, `손님${tag}`, `/r/${code}`);
  await a.waitForURL(/\/play\//);
  await b.waitForURL(/\/play\//);
  expect(a.url()).toBe(b.url());

  for (let move = 0; move < 144 && !(await gameOver(a, b)); move++) {
    await playOneMove(a, b);
  }

  await expect(a.locator(".result-card")).toBeVisible();
  await expect(b.locator(".result-card")).toBeVisible();
  await expect(a.getByText("고양이 25마리를 모두 찾았습니다")).toBeVisible();
  const scores = await a.locator(".seat-card .score").allTextContents();
  expect(scores.map(Number).reduce((sum, n) => sum + n, 0)).toBe(25); // 시간 초과가 없으면 점수 합은 찾은 고양이 수다
  await expect(a.locator(".rating-change")).toContainText("레이팅 1000 →");
  expect([...host.errors, ...guest.errors]).toEqual([]);
});
