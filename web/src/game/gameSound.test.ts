import type { Socket } from "socket.io-client";
import { afterEach, describe, expect, it, vi } from "vitest";

const playSound = vi.fn();
vi.mock("../sound/sound", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../sound/sound")>()),
  playSound: (kind: string) => playSound(kind),
}));

const { bindGameEvents, useGameStore } = await import("./gameStore");

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

afterEach(() => {
  playSound.mockClear();
  useGameStore.setState({ game: null });
});

describe("대국 효과음", () => {
  it("[성공] 칸이 열리면(내 수든 상대 수든) 열린 칸 종류에 맞는 소리를 낸다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("game:revealed", { gameId: "g1", seat: 1, move: { x: 0, y: 0 }, cells: [{ x: 0, y: 0, kind: "cat", seat: 1 }], scores: [0, 1], currentSeat: 1, turnDeadline: 1, version: 1 });
    trigger("game:revealed", { gameId: "g1", seat: 0, move: { x: 1, y: 0 }, cells: [{ x: 1, y: 0, kind: "number", n: 0 }], scores: [0, 1], currentSeat: 1, turnDeadline: 1, version: 2 });

    expect(playSound.mock.calls).toEqual([["cat"], ["dirt"]]);
  });
});
