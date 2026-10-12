import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../session/sessionStore";
import { ResumeCurrentGame } from "./resume";

const emit = vi.fn();
vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit }) }));

const player = { id: "p1", kind: "GUEST" as const, nickname: "냥냥이", skin1p: 16, skin2p: 17 };

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <ResumeCurrentGame />
      <Routes>
        <Route path="/" element={<p>로비</p>} />
        <Route path="/play/:gameId" element={<p>대국 화면</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  emit.mockClear();
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

describe("ResumeCurrentGame", () => {
  it("[성공] 진행 중인 대국이 있으면 대국 화면으로 이동하고 전체 상태를 요청한다", async () => {
    useSession.getState().setSession("token", player);
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ gameId: "g1" }), { status: 200 })));

    renderAt("/");

    await waitFor(() => expect(screen.getByText("대국 화면")).toBeTruthy());
    expect(emit).toHaveBeenCalledWith("game:sync", { gameId: "g1" });
  });

  it("[실패] 진행 중인 대국이 없으면(204) 그대로 둔다", async () => {
    useSession.getState().setSession("token", player);
    const fetchMock = vi.fn(async () => new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    renderAt("/");

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(screen.getByText("로비")).toBeTruthy();
    expect(emit).not.toHaveBeenCalled();
  });
});
