import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useRoomStore } from "../room/roomStore";
import { useSession } from "../session/sessionStore";
import { JoinRoomPage } from "./JoinRoomPage";

const emit = vi.fn();
vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit }) }));

afterEach(() => {
  cleanup();
  emit.mockClear();
  useRoomStore.getState().clearWaitingRoom();
  useSession.getState().clear();
});

describe("JoinRoomPage", () => {
  it("[성공] 방장이 자기 초대 링크를 열면 로비의 대기 화면으로 보낸다", () => {
    useSession.getState().setSession("token", { id: "host", kind: "GUEST", nickname: "방장냥", skin1p: 16, skin2p: 17 });
    useRoomStore.getState().setWaitingRoom({ code: "ABCDEF", status: "WAITING", expiresAt: 600_000 });

    render(
      <MemoryRouter initialEntries={["/r/ABCDEF"]}>
        <Routes>
          <Route path="/" element={<p>로비 화면</p>} />
          <Route path="/r/:code" element={<JoinRoomPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("로비 화면")).toBeTruthy();
  });
});
