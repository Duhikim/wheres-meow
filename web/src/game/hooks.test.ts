import { describe, expect, it } from "vitest";
import { gameIdToEnter } from "./hooks";
import type { GameState } from "./types";

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
