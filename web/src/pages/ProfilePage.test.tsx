import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProfilePage } from "./ProfilePage";

const profile = {
  id: "p1",
  nickname: "회원냥",
  kind: "MEMBER",
  skin: 18,
  rating: 1084,
  games: 6,
  wins: 4,
  losses: 1,
  draws: 1,
  ranked: true,
  recentGames: [
    {
      gameId: "g2",
      mode: "MATCH",
      endedAt: 1_700_000_000_000,
      opponentId: "p2",
      opponentNickname: "상대냥",
      myScore: 14,
      opponentScore: 11,
      result: "WIN",
      ratingBefore: 1068,
      ratingAfter: 1084,
    },
  ],
  botRecords: [
    { difficulty: "EASY", wins: 2, losses: 0, draws: 0 },
    { difficulty: "NORMAL", wins: 0, losses: 0, draws: 0 },
    { difficulty: "HARD", wins: 0, losses: 3, draws: 0 },
  ],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/players/:id" element={<ProfilePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProfilePage", () => {
  it("[성공] 레이팅, 전적, 최근 대국, 컴퓨터 대전 전적을 보여 준다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(profile), { status: 200 })));

    renderAt("/players/p1");

    await waitFor(() => expect(screen.getByText("회원냥")).toBeTruthy());
    expect(screen.getByText("1084")).toBeTruthy();
    expect(screen.getByText("4승 1패 1무")).toBeTruthy();
    expect(screen.getByText("상대냥")).toBeTruthy();
    expect(screen.getByText("승")).toBeTruthy();
    expect(screen.getByText("+16")).toBeTruthy();
    expect(screen.getByText("0승 3패 0무")).toBeTruthy();
  });

  it("[실패] 없는 플레이어면 안내 문구를 보여 준다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ code: "PLAYER_NOT_FOUND", message: "없음" }), { status: 404 })),
    );

    renderAt("/players/nobody");

    await waitFor(() => expect(screen.getByText("플레이어를 찾을 수 없습니다.")).toBeTruthy());
  });

  it("[성공] 게스트는 랭킹에 오르지 않는다는 안내를 보여 준다", async () => {
    const guest = { ...profile, kind: "GUEST", ranked: false };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(guest), { status: 200 })));

    renderAt("/players/p1");

    await waitFor(() => expect(screen.getByText(/게스트는 랭킹에 오르지 않습니다/)).toBeTruthy());
  });
});
