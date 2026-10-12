import { describe, expect, it } from "vitest";
import { turnTimer } from "./timer";

describe("turnTimer", () => {
  it("[성공] 남은 시간을 20초에 대한 비율로 매끄럽게 계산한다(초 단위로 끊지 않는다)", () => {
    expect(turnTimer(20_000, 0).fraction).toBe(1);
    expect(turnTimer(20_000, 10_500).fraction).toBeCloseTo(0.475);
    expect(turnTimer(20_000, 10_600).fraction).toBeCloseTo(0.47);
  });

  it("[성공] 5초 이하로 남으면 급함 상태가 된다", () => {
    expect(turnTimer(20_000, 14_999).urgent).toBe(false);
    expect(turnTimer(20_000, 15_000).urgent).toBe(true);
  });

  it("[성공] 마감이 지나면 0 이고, 시계가 어긋나 20초보다 많이 남아도 1 을 넘지 않는다", () => {
    expect(turnTimer(20_000, 25_000).fraction).toBe(0);
    expect(turnTimer(30_000, 0).fraction).toBe(1);
  });

  it("[성공] 남은 초는 올림으로 보여 준다", () => {
    expect(turnTimer(20_000, 10_500).seconds).toBe(10);
    expect(turnTimer(20_000, 10_001).seconds).toBe(10);
    expect(turnTimer(20_000, 9_999).seconds).toBe(11);
  });
});
