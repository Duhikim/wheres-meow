import { expect, test } from "@playwright/test";
import { newPlayer, stamp } from "./support";

test("가입하면 새로고침해도 로그인이 유지되고, 로그아웃 뒤 다시 로그인할 수 있다", async ({ browser }) => {
  const { page, errors } = await newPlayer(browser);
  const tag = stamp();
  const username = `e2e_${tag}`;

  await page.goto("/signup");
  await page.getByLabel(/아이디/).fill(username);
  await page.getByLabel(/^비밀번호 \(/).fill("password123");
  await page.getByLabel("비밀번호 확인").fill("password12");
  await page.getByRole("button", { name: "가입하기" }).click();
  await expect(page.locator(".error").first()).toHaveText("비밀번호가 서로 다릅니다.");
  await page.getByLabel("비밀번호 확인").fill("password123");
  await page.getByLabel(/닉네임/).fill(`회원${tag}`);
  await page.getByRole("button", { name: "가입하기" }).click();
  await expect(page.locator(".who")).toContainText(`회원${tag}`);
  await expect(page.locator(".who")).toContainText("회원");

  await page.reload();
  await expect(page.getByRole("button", { name: "로그아웃" })).toBeVisible();

  await page.getByRole("button", { name: "로그아웃" }).click();
  await expect(page.locator("#nickname")).toBeVisible();

  await page.goto("/login");
  await page.getByLabel("아이디").fill(username);
  await page.getByLabel("비밀번호").fill("wrong-password");
  await page.getByRole("button", { name: "로그인" }).click();
  await expect(page.locator(".error")).toHaveText("아이디 또는 비밀번호가 맞지 않습니다.");
  await page.getByLabel("비밀번호").fill("password123");
  await page.getByRole("button", { name: "로그인" }).click();
  await expect(page.getByRole("button", { name: "로그아웃" })).toBeVisible();

  await page.getByRole("link", { name: /랭킹/ }).click();
  await expect(page.getByRole("heading", { name: "랭킹" })).toBeVisible();
  expect(errors).toEqual([]);
});
