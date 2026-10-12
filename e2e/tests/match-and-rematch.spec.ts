import { expect, test } from "@playwright/test";
import { enterAsGuest, forfeit, newPlayer, startQuickMatch, stamp } from "./support";

test("빠른 대전으로 만나 레이팅이 반영되고, 재대결은 선공을 바꿔 새 대국으로 이어진다", async ({ browser }) => {
  const tag = stamp();
  const first = await newPlayer(browser);
  const second = await newPlayer(browser);
  const a = first.page;
  const b = second.page;
  await enterAsGuest(a, `에이${tag}`);
  await enterAsGuest(b, `비${tag}`);

  // 대기를 취소하면 로비로 돌아온다
  await a.getByRole("button", { name: /빠른 대전/ }).click();
  await expect(a.getByText("레이팅 ±100 안에서 찾고 있습니다")).toBeVisible();
  await a.getByRole("button", { name: "취소" }).click();
  await expect(a.getByRole("button", { name: /빠른 대전/ })).toBeVisible();

  await startQuickMatch(a, b);
  const firstGame = a.url();
  expect(b.url()).toBe(firstGame);
  const aStartedFirst = (await a.locator(".turn-label").textContent())?.includes("내 차례");

  await forfeit(b);
  await expect(a.locator(".rating-change")).toContainText("레이팅 1000 → 1016 (+16)");
  await expect(b.locator(".rating-change")).toContainText("레이팅 1000 → 984 (-16)");

  // 재대결: 신청 → 상대 수락 → 같은 두 사람의 새 대국, 선공 교대
  await a.getByRole("button", { name: "재대결 신청" }).click();
  await expect(a.getByText(/상대의 응답을 기다리는 중/)).toBeVisible();
  await b.getByRole("button", { name: "수락" }).click();
  await a.waitForURL((url) => url.toString() !== firstGame);
  await expect(a.locator(".result-card")).toHaveCount(0);
  expect(b.url()).toBe(a.url());
  expect((await a.locator(".turn-label").textContent())?.includes("내 차례")).toBe(!aStartedFirst);

  // 거절하면 신청한 쪽에 사유가 보인다
  await forfeit(a);
  await b.getByRole("button", { name: "재대결 신청" }).click();
  await a.getByRole("button", { name: "거절" }).click();
  await expect(b.getByText("상대가 재대결을 거절했습니다.")).toBeVisible();
  await expect(a.getByText("재대결을 거절했습니다.", { exact: true })).toBeVisible();
  await expect(a.getByRole("button", { name: "수락" })).toHaveCount(0);

  // 내 전적: 매칭 2판이 최근 대국에 있다
  await a.getByRole("link", { name: "로비로" }).click();
  await a.getByRole("link", { name: /내 전적/ }).click();
  await expect(a.locator(".recent-row.win, .recent-row.loss")).toHaveCount(2);
  expect([...first.errors, ...second.errors]).toEqual([]);
});

test("결과 화면을 떠나면 상대의 재대결 버튼이 꺼진다", async ({ browser }) => {
  const tag = stamp();
  const first = await newPlayer(browser);
  const second = await newPlayer(browser);
  const a = first.page;
  const b = second.page;
  await enterAsGuest(a, `떠남${tag}`);
  await enterAsGuest(b, `남음${tag}`);
  await startQuickMatch(a, b);

  await forfeit(a);
  await expect(b.locator(".result-card")).toBeVisible();
  await a.getByRole("link", { name: "로비로" }).click();

  await expect(b.getByText("상대가 결과 화면을 떠났습니다.")).toBeVisible();
  await expect(b.getByRole("button", { name: "재대결 신청" })).toHaveCount(0);
});
