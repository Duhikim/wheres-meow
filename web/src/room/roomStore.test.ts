import type { Socket } from "socket.io-client";
import { afterEach, describe, expect, it } from "vitest";
import { bindGameEvents } from "../game/gameStore";
import { useRoomStore } from "./roomStore";

/** on() 으로 등록한 핸들러를 trigger() 로 직접 부르는 최소 가짜 소켓. */
function fakeSocket() {
  const handlers: Record<string, (payload: unknown) => void> = {};
  const socket = {
    on: (name: string, handler: (payload: unknown) => void) => {
      handlers[name] = handler;
      return socket;
    },
  };
  return { socket: socket as unknown as Socket, trigger: (name: string, payload: unknown) => handlers[name](payload) };
}

const waiting = { code: "ABCDEF", status: "WAITING", expiresAt: 600_000 };

afterEach(() => useRoomStore.getState().clearWaitingRoom());

describe("대기 중인 방 상태", () => {
  it("[성공] room:waiting 을 받으면 대기 중인 방을 기억한다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);

    trigger("room:waiting", waiting);

    expect(useRoomStore.getState().waitingRoom).toEqual(waiting);
  });

  it("[성공] 대국이 시작되면 대기 중인 방을 지운다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("room:waiting", waiting);

    trigger("game:started", {
      gameId: "g1", mode: "INVITE", mySeat: 0,
      seats: [{ nickname: "a", skin: 16, score: 0 }, { nickname: "b", skin: 17, score: 0 }],
      currentSeat: 0, turnDeadline: 1, version: 0, cells: [],
    });

    expect(useRoomStore.getState().waitingRoom).toBeNull();
  });

  it("[성공] 방이 만료되었다는 오류를 받으면 대기 중인 방을 지운다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("room:waiting", waiting);

    trigger("error", { code: "ROOM_EXPIRED", message: "" });

    expect(useRoomStore.getState().waitingRoom).toBeNull();
  });

  it("[실패] 방과 무관한 오류로는 대기 중인 방을 지우지 않는다", () => {
    const { socket, trigger } = fakeSocket();
    bindGameEvents(socket);
    trigger("room:waiting", waiting);

    trigger("error", { code: "NOT_YOUR_TURN", message: "" });

    expect(useRoomStore.getState().waitingRoom).toEqual(waiting);
  });
});
