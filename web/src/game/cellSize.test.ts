import { describe, expect, it } from "vitest";
import { computeCellSize } from "./cellSize";

describe("computeCellSize", () => {
  it("[성공] 폭 360px 폰에서는 28px 이다", () => {
    expect(computeCellSize(360)).toBe(28);
  });

  it("[성공] 넓은 화면에서는 40px 로 제한한다", () => {
    expect(computeCellSize(1440)).toBe(40);
  });

  it("[성공] 폭 320px 작은 폰에서도 칸이 화면 안에 들어간다", () => {
    expect(computeCellSize(320) * 12).toBeLessThanOrEqual(320 - 24);
  });
});
