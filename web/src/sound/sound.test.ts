import { describe, expect, it } from "vitest";
import { MEOW_FILES, pickMeow, soundKindOfCells } from "./sound";

describe("soundKindOfCells", () => {
  it("[성공] 고양이를 찾았으면 고양이 소리다", () => {
    expect(soundKindOfCells([{ x: 0, y: 0, kind: "cat", seat: 0 }])).toBe("cat");
  });

  it("[성공] 숫자 칸이 하나라도 열렸으면 발자국 소리다(연쇄로 빈 칸이 함께 열려도)", () => {
    expect(
      soundKindOfCells([
        { x: 0, y: 0, kind: "number", n: 0 },
        { x: 1, y: 0, kind: "number", n: 2 },
      ]),
    ).toBe("paw");
  });

  it("[성공] 빈 흙만 열렸으면 흙 소리다", () => {
    expect(soundKindOfCells([{ x: 0, y: 0, kind: "number", n: 0 }])).toBe("dirt");
  });

  it("[실패] 열린 칸이 없으면 소리를 내지 않는다", () => {
    expect(soundKindOfCells([])).toBeNull();
  });
});

describe("pickMeow", () => {
  it("[성공] 고른 울음 6개 중 하나를 고르고, 난수 범위 양 끝에서도 목록 안에 있다", () => {
    expect(MEOW_FILES).toHaveLength(6);
    expect(pickMeow(() => 0)).toBe(MEOW_FILES[0]);
    expect(pickMeow(() => 0.9999)).toBe(MEOW_FILES[5]);
    expect(MEOW_FILES).toContain(pickMeow(() => 0.5));
  });
});
