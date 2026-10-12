import { describe, expect, it } from "vitest";
import { catSvg, grassSvg, pawSvg } from "./svg";
import { ALLOWED_SKINS, DEFAULT_SKIN_1P, DEFAULT_SKIN_2P, SKINS } from "./skins";

describe("skins", () => {
  it("[성공] 확정한 스킨 10종과 기본값 16·17 을 가진다", () => {
    expect([...ALLOWED_SKINS].sort((a, b) => a - b)).toEqual([9, 10, 11, 12, 16, 17, 18, 19, 20, 21]);
    expect([DEFAULT_SKIN_1P, DEFAULT_SKIN_2P]).toEqual([16, 17]);
    expect(Object.keys(SKINS)).toHaveLength(10);
  });
});

describe("catSvg", () => {
  it("[성공] 모든 스킨을 풀숲 빼꼼 자세와 얼굴 자세로 그린다", () => {
    for (const skin of ALLOWED_SKINS) {
      expect(catSvg(skin, "peek", "a")).toMatch(/^<svg viewBox="0 0 100 100">.*<\/svg>$/s);
      expect(catSvg(skin, "face", "a")).toMatch(/^<svg/);
    }
  });

  it("[성공] 빼꼼 자세에는 앞쪽 풀잎이 있고 얼굴 자세에는 없다", () => {
    expect(catSvg(16, "peek", "a")).toContain("#3f7a1f");
    expect(catSvg(16, "face", "a")).not.toContain("#3f7a1f");
  });

  it("[성공] 고유 접두사를 clipPath ID 에 넣어 한 화면의 여러 고양이가 겹치지 않는다", () => {
    expect(catSvg(18, "peek", "x1")).toContain('id="x1-head"');
    expect(catSvg(18, "peek", "x2")).toContain('id="x2-head"');
  });

  it("[실패] 허용하지 않는 스킨이면 오류를 던진다", () => {
    expect(() => catSvg(13, "peek", "a")).toThrow(/13/);
  });
});

describe("grassSvg", () => {
  it("[성공] 같은 칸 번호면 항상 같은 들풀을 그린다", () => {
    expect(grassSvg(37)).toBe(grassSvg(37));
  });

  it("[성공] 칸 번호가 다르면 모양이 다르다", () => {
    expect(grassSvg(37)).not.toBe(grassSvg(38));
  });
});

describe("pawSvg", () => {
  it("[성공] 발자국 위에 숫자를 쓴다", () => {
    expect(pawSvg(3)).toContain(">3</text>");
  });

  it("[실패] 1~8 이 아니면 오류를 던진다", () => {
    expect(() => pawSvg(0)).toThrow();
    expect(() => pawSvg(9)).toThrow();
  });
});
