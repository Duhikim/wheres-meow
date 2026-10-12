import type { Socket } from "socket.io-client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { bindGameEvents, useGameStore } from "../game/gameStore";
import { useMatchStore } from "./matchStore";

function fakeSocket() {
  const handlers: Record<string, (payload?: unknown) => void> = {};
  const emit = vi.fn();
  const socket = {
    emit,
    on: (name: string, handler: (payload?: unknown) => void) => {
      handlers[name] = handler;
      return socket;
    },
  };
  return { socket: socket as unknown as Socket, emit, trigger: (name: string, payload?: unknown) => handlers[name](payload) };
}

afterEach(() => {
  useMatchStore.getState().clearWaiting();
  useGameStore.setState({ connection: "connected", lastError: null, game: null });
});

describe("매칭 대기 이벤트", () => {
  it("[성공] match:waiting 을 받으면 대기 상태가 된다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("match:waiting", { since: 1000, range: 100 });

    expect(useMatchStore.getState().waiting).toEqual({ since: 1000, range: 100 });
  });

  it("[성공] 대국이 시작되면 대기 상태를 지운다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("match:waiting", { since: 1000, range: 100 });

    trigger("game:started", {
      gameId: "g1", mode: "MATCH", mySeat: 0, seats: [], currentSeat: 0, turnDeadline: 1, version: 0, cells: [],
    });

    expect(useMatchStore.getState().waiting).toBeNull();
  });

  it("[실패] 대국 중이라 대기열에 못 들어가면 대기 상태를 지운다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("match:waiting", { since: 1000, range: 100 });

    trigger("error", { code: "ALREADY_IN_GAME" });

    expect(useMatchStore.getState().waiting).toBeNull();
  });

  it("[성공] 대기 중에 연결이 끊겼다 다시 붙으면 대기열에 다시 들어간다(서버는 끊긴 사람을 뺀다)", () => {
    const { socket, emit, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("match:waiting", { since: 1000, range: 100 });

    trigger("connect");

    expect(emit).toHaveBeenCalledWith("match:join");
  });

  it("[성공] 다시 줄을 섰는데 이미 대기 중이라는 응답이면 오류로 보지 않고 계속 기다린다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("match:waiting", { since: 1000, range: 100 });

    trigger("error", { code: "ALREADY_QUEUED" });

    expect(useGameStore.getState().lastError).toBeNull();
    expect(useMatchStore.getState().waiting).not.toBeNull();
  });
});
