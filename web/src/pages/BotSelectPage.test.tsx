import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../session/sessionStore";
import { BotSelectPage } from "./BotSelectPage";

const emit = vi.fn();
vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit }) }));

const player = { id: "p1", kind: "GUEST" as const, nickname: "냥냥이", skin1p: 16, skin2p: 17 };
const records = [
  { difficulty: "EASY", wins: 3, losses: 0, draws: 0 },
  { difficulty: "NORMAL", wins: 1, losses: 2, draws: 0 },
  { difficulty: "HARD", wins: 0, losses: 4, draws: 1 },
];

afterEach(() => {
  cleanup();
  emit.mockClear();
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

function renderPage() {
  render(
    <MemoryRouter>
      <BotSelectPage />
    </MemoryRouter>,
  );
}

describe("BotSelectPage", () => {
  it("[성공] 난이도 세 개와 내 전적을 보여 준다", async () => {
    useSession.getState().setSession("token", player);
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(records), { status: 200 })));

    renderPage();

    await waitFor(() => expect(screen.getByText("0승 4패 1무")).toBeTruthy());
    expect(screen.getByText("3승 0패 0무")).toBeTruthy();
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("[성공] 난이도를 누르면 그 난이도로 컴퓨터 대전을 시작한다", async () => {
    useSession.getState().setSession("token", player);
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(records), { status: 200 })));
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: /어려움/ }));

    expect(emit).toHaveBeenCalledWith("bot:start", { difficulty: "HARD" });
  });
});
