import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cancelLeaveResult, scheduleLeaveResult } from "./leaveResult";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("결과 화면 이탈 알림", () => {
  it("[성공] 화면을 떠나면 다음 틱에 알린다", () => {
    const send = vi.fn();

    scheduleLeaveResult("g1", send);
    vi.runAllTimers();

    expect(send).toHaveBeenCalledOnce();
  });

  it("[성공] 같은 대국 화면이 곧바로 다시 붙으면(StrictMode 재실행) 알리지 않는다", () => {
    const send = vi.fn();

    scheduleLeaveResult("g1", send);
    cancelLeaveResult("g1");
    vi.runAllTimers();

    expect(send).not.toHaveBeenCalled();
  });

  it("[성공] 다른 대국 화면이 붙으면 이전 대국 이탈은 그대로 알린다", () => {
    const send = vi.fn();

    scheduleLeaveResult("g1", send);
    cancelLeaveResult("g2");
    vi.runAllTimers();

    expect(send).toHaveBeenCalledOnce();
  });
});
