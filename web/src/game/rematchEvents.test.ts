import type { Socket } from "socket.io-client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { bindGameEvents, useGameStore } from "./gameStore";

function fakeSocket() {
  const handlers: Record<string, (payload?: unknown) => void> = {};
  const socket = {
    emit: vi.fn(),
    on: (name: string, handler: (payload?: unknown) => void) => {
      handlers[name] = handler;
      return socket;
    },
  };
  return { socket: socket as unknown as Socket, trigger: (name: string, payload?: unknown) => handlers[name](payload) };
}

afterEach(() => useGameStore.setState({ game: null, lastError: null, rematch: null }));

describe("재대결 이벤트", () => {
  it("[성공] 상대가 신청하면 상대 신청 상태가 된다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("game:rematch-requested", { gameId: "g1" });

    expect(useGameStore.getState().rematch).toEqual({ gameId: "g1", mine: false, theirs: true, cancelled: null });
  });

  it("[성공] 내가 신청하면 내 신청 상태가 된다", () => {
    useGameStore.getState().markRematchRequested("g1");

    expect(useGameStore.getState().rematch).toEqual({ gameId: "g1", mine: true, theirs: false, cancelled: null });
  });

  it("[성공] 취소되면 사유를 남긴다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    useGameStore.getState().markRematchRequested("g1");

    trigger("game:rematch-cancelled", { gameId: "g1", reason: "DECLINED" });

    expect(useGameStore.getState().rematch?.cancelled).toBe("DECLINED");
  });

  it("[성공] 새 대국이 시작되면 재대결 상태를 지운다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("game:rematch-requested", { gameId: "g1" });

    trigger("game:started", { gameId: "g2", mode: "INVITE", mySeat: 0, seats: [], currentSeat: 1, turnDeadline: 1, version: 0, cells: [] });

    expect(useGameStore.getState().rematch).toBeNull();
  });

  it("[성공] 내가 거절하면 수락·거절 대신 거절했다는 상태가 된다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("game:rematch-requested", { gameId: "g1" });

    useGameStore.getState().markRematchDeclined("g1");

    expect(useGameStore.getState().rematch?.cancelled).toBe("I_DECLINED");
  });

  it("[실패] 내 신청을 서버가 만료로 거부하면 기다림을 멈추고 만료 상태가 된다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    useGameStore.getState().markRematchRequested("g1");

    trigger("error", { code: "REMATCH_EXPIRED" });

    expect(useGameStore.getState().rematch?.cancelled).toBe("EXPIRED");
  });
});
