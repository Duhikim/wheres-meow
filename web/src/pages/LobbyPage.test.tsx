import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useMatchStore } from "../match/matchStore";
import { useRoomStore } from "../room/roomStore";
import { useSession } from "../session/sessionStore";
import { LobbyPage } from "./LobbyPage";

const emit = vi.fn();
vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit }) }));

afterEach(() => {
  cleanup();
  emit.mockClear();
  useRoomStore.getState().clearWaitingRoom();
  useMatchStore.getState().clearWaiting();
  useSession.getState().clear();
});

const guest = { id: "p1", kind: "GUEST" as const, nickname: "방장냥", skin1p: 16, skin2p: 17 };

function renderLobby() {
  render(
    <MemoryRouter>
      <LobbyPage />
    </MemoryRouter>,
  );
}

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

  it("[성공] 빠른 대전을 누르면 대기열에 들어간다", () => {
    useSession.getState().setSession("token", guest);
    renderLobby();

    fireEvent.click(screen.getByRole("button", { name: /빠른 대전/ }));

    expect(emit).toHaveBeenCalledWith("match:join");
  });

  it("[성공] 매칭 대기 중이면 상대를 찾는 화면과 취소 버튼을 보여 주고, 취소하면 대기열에서 나온다", () => {
    useSession.getState().setSession("token", guest);
    useMatchStore.getState().setWaiting({ since: Date.now(), range: 100 });
    renderLobby();

    expect(screen.getByText("상대를 찾는 중")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "취소" }));

    expect(emit).toHaveBeenCalledWith("match:leave");
    expect(useMatchStore.getState().waiting).toBeNull();
  });

  it("[성공] 랭킹과 내 프로필로 가는 링크가 있다", () => {
    useSession.getState().setSession("token", guest);
    renderLobby();

    expect(screen.getByRole("link", { name: /랭킹/ }).getAttribute("href")).toBe("/ranking");
    expect(screen.getByRole("link", { name: /내 전적/ }).getAttribute("href")).toBe("/players/p1");
  });
});
