import { expect, test } from "@playwright/test";
import { enterAsGuest, forfeit, newPlayer, stamp } from "./support";

test("컴퓨터와 대결하고, 재대결은 바로 시작되며, 전적은 레이팅과 따로 쌓인다", async ({ browser }) => {
  const { page, errors } = await newPlayer(browser);
  await enterAsGuest(page, `혼자${stamp()}`);

  await page.getByRole("link", { name: /컴퓨터와 대결/ }).click();
  await page.getByRole("button", { name: /쉬움/ }).click();
  await page.waitForURL(/\/play\//);
  const firstGame = page.url();
  await expect(page.locator(".seat-card").nth(1)).toContainText("컴퓨터 (쉬움)");

  await forfeit(page);
  await expect(page.locator(".result-card")).toContainText("패배");
  await expect(page.locator(".rating-change")).toHaveCount(0); // 컴퓨터 대전은 레이팅에 반영하지 않는다

  await page.getByRole("button", { name: "재대결 신청" }).click();
  await page.waitForURL((url) => url.toString() !== firstGame);
  await forfeit(page);
  await expect(page.locator(".result-card")).toBeVisible();

  await page.getByRole("link", { name: "로비로" }).click();
  await page.getByRole("link", { name: /내 전적/ }).click();
  await expect(page.locator(".profile-rating b")).toHaveText("1000");
  await expect(page.locator(".recent-row", { hasText: "쉬움" })).toContainText("0승 2패 0무");
  expect(errors).toEqual([]);
});
