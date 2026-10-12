import { describe, expect, it } from "vitest";
import { formatDuration } from "./format";

describe("formatDuration", () => {
  it("[성공] 1분 미만은 초와 소수 한 자리로 보여 준다", () => {
    expect(formatDuration(41_234)).toBe("41.2초");
    expect(formatDuration(1_000)).toBe("1.0초");
  });

  it("[성공] 1분 이상은 분:초.소수로 보여 준다", () => {
    expect(formatDuration(83_450)).toBe("1:23.4");
    expect(formatDuration(600_000)).toBe("10:00.0");
  });

  it("[성공] 기록이 없으면 대시를 보여 준다", () => {
    expect(formatDuration(null)).toBe("—");
  });
});
