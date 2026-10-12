import { describe, expect, it } from "vitest";
import { currentRange } from "./matchStore";

describe("currentRange", () => {
  it("[성공] 처음 범위에서 5초마다 50씩 넓어진다", () => {
    expect(currentRange(100, 0)).toBe(100);
    expect(currentRange(100, 4)).toBe(100);
    expect(currentRange(100, 5)).toBe(150);
    expect(currentRange(100, 29)).toBe(350);
  });

  it("[성공] 30초가 지나면 제한이 없다", () => {
    expect(currentRange(100, 30)).toBeNull();
  });

  it("[성공] 처음부터 제한이 없으면 계속 없다", () => {
    expect(currentRange(null, 0)).toBeNull();
  });
});
