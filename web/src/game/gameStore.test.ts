import type { Socket } from "socket.io-client";
import { afterEach, describe, expect, it } from "vitest";
import { bindGameEvents, useGameStore } from "./gameStore";

function fakeSocket() {
  const handlers: Record<string, (payload?: unknown) => void> = {};
  const socket = {
    on: (name: string, handler: (payload?: unknown) => void) => {
      handlers[name] = handler;
      return socket;
    },
  };
  return { socket: socket as unknown as Socket, trigger: (name: string, payload?: unknown) => handlers[name](payload) };
}

afterEach(() => useGameStore.setState({ connection: "connected", lastError: null }));

describe("연결 상태", () => {
  it("[성공] 연결이 끊기면 다시 연결하는 중으로 바뀐다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("disconnect", "transport close");

    expect(useGameStore.getState().connection).toBe("reconnecting");
  });

  it("[성공] 다시 연결되면 연결됨으로 돌아온다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("disconnect", "transport close");

    trigger("connect");

    expect(useGameStore.getState().connection).toBe("connected");
  });

  it("[실패] 직접 연결을 끊은 경우(토큰 교체 등)는 재연결 중으로 보지 않는다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("disconnect", "io client disconnect");

    expect(useGameStore.getState().connection).toBe("connected");
  });
});
