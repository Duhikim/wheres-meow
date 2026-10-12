import { expect, test } from "@playwright/test";
import { newGame, reveal, seededRandom } from "../../web/src/single/engine";
import { enterAsGuest, newPlayer, stamp } from "./support";

test("혼자 연습: 시드 판을 끝까지 깨면 최고 기록이 남고, 고급 판도 휴대폰 폭에 들어간다", async ({ browser }) => {
  const { page, errors } = await newPlayer(browser);
  await enterAsGuest(page, `연습${stamp()}`);

  await page.getByRole("link", { name: /혼자 연습/ }).click();
  await expect(page.getByRole("link", { name: /초급/ })).toContainText("기록 없음");

  // 시드로 판을 고정하고, 같은 엔진으로 고양이 위치를 계산해 안전한 칸만 연다
  const seed = 11;
  await page.goto(`/single/BEGINNER?seed=${seed}`);
  const cats = reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(seed)).cats!;
  await page.getByRole("button", { name: "4,4", exact: true }).click();
  await page.waitForTimeout(1_100); // 서버는 1초 미만의 클리어를 조작된 값으로 거부한다
  for (let y = 0; y < 9; y++) {
    for (let x = 0; x < 9; x++) {
      if (cats.has(`${x},${y}`)) continue;
      const cell = page.getByRole("button", { name: `${x},${y}`, exact: true });
      if ((await cell.getAttribute("class"))?.includes("closed")) await cell.click();
    }
  }
  await expect(page.getByRole("heading", { name: "성공!" })).toBeVisible();
  await expect(page.getByText("최고 기록을 새로 세웠습니다!")).toBeVisible();

  await page.getByRole("link", { name: "난이도 선택" }).click();
  await expect(page.getByRole("link", { name: /초급/ })).toContainText("최고");

  await page.getByRole("link", { name: /고급/ }).click();
  await expect(page.getByRole("button", { name: /^\d+,\d+$/ })).toHaveCount(12 * 16);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});
