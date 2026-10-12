import { describe, expect, it } from "vitest";
import { gameReducer } from "./gameReducer";
import type { GameState, StartedPayload } from "./types";

const started: StartedPayload = {
  gameId: "g1",
  mode: "INVITE",
  mySeat: 1,
  seats: [
    { nickname: "방장냥", skin: 16, score: 0 },
    { nickname: "손님냥", skin: 17, score: 0 },
  ],
  currentSeat: 0,
  turnDeadline: 20_000,
  version: 0,
  cells: [],
};

const start = (): GameState => gameReducer(null, { type: "started", payload: started })!;

describe("gameReducer", () => {
  describe("started", () => {
    it("[성공] 시작 페이로드로 새 상태를 만든다", () => {
      const state = start();

      expect(state.mySeat).toBe(1);
      expect(state.status).toBe("IN_PROGRESS");
      expect(state.cells).toEqual({});
    });
  });

  describe("revealed", () => {
    it("[성공] 열린 칸과 점수, 다음 턴을 반영한다", () => {
      const state = gameReducer(start(), {
        type: "revealed",
        payload: {
          gameId: "g1",
          seat: 0,
          cells: [
            { x: 3, y: 4, kind: "cat", seat: 0 },
            { x: 0, y: 0, kind: "number", n: 2 },
          ],
          scores: [1, 0],
          currentSeat: 0,
          turnDeadline: 40_000,
          version: 1,
        },
      })!;

      expect(state.cells["3,4"]).toEqual({ kind: "cat", seat: 0 });
      expect(state.cells["0,0"]).toEqual({ kind: "number", n: 2 });
      expect(state.seats[0].score).toBe(1);
      expect(state.turnDeadline).toBe(40_000);
      expect(state.version).toBe(1);
    });

    it("[실패] version 이 건너뛰면 적용하지 않고 outOfSync 로 표시한다", () => {
      const before = start();

      const state = gameReducer(before, {
        type: "revealed",
        payload: { gameId: "g1", seat: 0, cells: [], scores: [5, 5], currentSeat: 1, turnDeadline: 1, version: 2 },
      })!;

      expect(state.outOfSync).toBe(true);
      expect(state.seats[0].score).toBe(0);
      expect(state.version).toBe(0);
    });

    it("[실패] 다른 대국의 이벤트는 무시한다", () => {
      const before = start();

      const state = gameReducer(before, {
        type: "revealed",
        payload: { gameId: "other", seat: 0, cells: [], scores: [1, 0], currentSeat: 1, turnDeadline: 1, version: 1 },
      });

      expect(state).toBe(before);
    });
  });

  describe("timeout", () => {
    it("[성공] 감점과 턴 넘김을 반영한다", () => {
      const state = gameReducer(start(), {
        type: "timeout",
        payload: { gameId: "g1", seat: 0, scores: [-1, 0], currentSeat: 1, turnDeadline: 60_000, version: 1 },
      })!;

      expect(state.seats[0].score).toBe(-1);
      expect(state.currentSeat).toBe(1);
    });
  });

  describe("ended (version 누락 후)", () => {
    it("[성공] outOfSync 상태여도 종료 이벤트는 최종 상태이므로 적용한다", () => {
      const outOfSync = { ...start(), outOfSync: true };

      const state = gameReducer(outOfSync, {
        type: "ended",
        payload: { gameId: "g1", reason: "ALL_FOUND", winner: 1, scores: [10, 15], cats: [[2, 2]], version: 9 },
      })!;

      expect(state.status).toBe("FINISHED");
      expect(state.result).toEqual({ reason: "ALL_FOUND", winner: 1 });
      expect(state.seats[1].score).toBe(15);
      expect(state.version).toBe(9);
    });
  });

  describe("ended", () => {
    it("[성공] 결과를 기록하고 아무도 못 찾은 고양이를 공개한다", () => {
      const afterReveal = gameReducer(start(), {
        type: "revealed",
        payload: {
          gameId: "g1",
          seat: 0,
          cells: [{ x: 1, y: 1, kind: "cat", seat: 0 }],
          scores: [1, 0],
          currentSeat: 0,
          turnDeadline: 1,
          version: 1,
        },
      });

      const state = gameReducer(afterReveal, {
        type: "ended",
        payload: { gameId: "g1", reason: "FORFEIT", winner: 0, scores: [1, 0], cats: [[1, 1], [2, 2]], version: 2 },
      })!;

      expect(state.status).toBe("FINISHED");
      expect(state.result).toEqual({ reason: "FORFEIT", winner: 0 });
      expect(state.cells["1,1"]).toEqual({ kind: "cat", seat: 0 });
      expect(state.cells["2,2"]).toEqual({ kind: "cat", seat: null });
      expect(state.turnDeadline).toBeNull();
    });
  });
});
