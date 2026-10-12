import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { gameIdToEnter, useSecondsLeft } from "./hooks";
import type { GameState } from "./types";

afterEach(() => vi.useRealTimers());

describe("useSecondsLeft", () => {
  it("[성공] 숨겨진 탭에서 타이머가 멈춰 있다가 마감 시각이 바뀌어도 지금 시각 기준으로 계산한다", () => {
    vi.useFakeTimers();
    vi.setSystemTime(0);
    const { result, rerender } = renderHook(({ deadline }) => useSecondsLeft(deadline), {
      initialProps: { deadline: 20_000 },
    });

    // 탭이 숨겨져 간격 타이머가 돌지 않은 채 30초가 흐른 뒤 새 턴(마감 = 지금 + 20초)이 왔다
    vi.setSystemTime(30_000);
    rerender({ deadline: 50_000 });

    expect(result.current).toBe(20);
  });

  it("[성공] 마감이 없으면 null 이다", () => {
    const { result } = renderHook(() => useSecondsLeft(null));

    expect(result.current).toBeNull();
  });
});

const base: GameState = {
  gameId: "g1",
  mode: "INVITE",
  mySeat: 0,
  seats: [
    { nickname: "a", skin: 16, score: 0 },
    { nickname: "b", skin: 17, score: 0 },
  ],
  currentSeat: 0,
  turnDeadline: 1,
  version: 0,
  cells: {},
  status: "IN_PROGRESS",
  result: null,
  outOfSync: false,
      lastMove: null,
};

describe("gameIdToEnter", () => {
  it("[성공] 진행 중인 대국이면 그 대국으로 들어간다", () => {
    expect(gameIdToEnter(base)).toBe("g1");
  });

  it("[실패] 화면이 서버와 어긋난 대국으로는 다시 끌고 가지 않는다", () => {
    expect(gameIdToEnter({ ...base, outOfSync: true })).toBeNull();
  });

  it("[실패] 끝난 대국으로는 들어가지 않는다", () => {
    expect(gameIdToEnter({ ...base, status: "FINISHED" })).toBeNull();
  });

  it("[실패] 대국이 없으면 아무 데도 가지 않는다", () => {
    expect(gameIdToEnter(null)).toBeNull();
  });
});
