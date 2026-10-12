import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useRoomStore } from "../room/roomStore";
import { useSession } from "../session/sessionStore";
import { LobbyPage } from "./LobbyPage";

const emit = vi.fn();
vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit }) }));

afterEach(() => {
  cleanup();
  emit.mockClear();
  useRoomStore.getState().clearWaitingRoom();
  useSession.getState().clear();
});

describe("LobbyPage", () => {
  it("[성공] 대기 중에 새로고침해도 방에 다시 들어가 대기 화면을 이어 간다", () => {
    useSession.getState().setSession("token", { id: "p1", kind: "GUEST", nickname: "방장냥", skin1p: 16, skin2p: 17 });
    useRoomStore.getState().setWaitingRoom({ code: "ABCDEF", status: "WAITING", expiresAt: 600_000 });

    render(
      <MemoryRouter>
        <LobbyPage />
      </MemoryRouter>,
    );

    expect(emit).toHaveBeenCalledWith("room:join", { code: "ABCDEF" });
    expect(screen.getByText("친구를 기다리는 중")).toBeTruthy();
  });

  it("[실패] 대기 중인 방이 없으면 방에 들어가지 않는다", () => {
    useSession.getState().setSession("token", { id: "p1", kind: "GUEST", nickname: "방장냥", skin1p: 16, skin2p: 17 });

    render(
      <MemoryRouter>
        <LobbyPage />
      </MemoryRouter>,
    );

    expect(emit).not.toHaveBeenCalledWith("room:join", expect.anything());
  });
});
