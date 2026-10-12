import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RankingPage } from "./RankingPage";

function entry(rank: number, nickname: string, rating: number) {
  return { rank, playerId: `p${rank}`, nickname, skin: 16, rating, games: 7, wins: 5, losses: 2, draws: 0 };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderPage() {
  render(
    <MemoryRouter>
      <RankingPage />
    </MemoryRouter>,
  );
}

describe("RankingPage", () => {
  it("[성공] 순위, 닉네임, 레이팅, 전적을 보여 주고 프로필로 연결한다", async () => {
    const body = { page: 1, totalPages: 1, entries: [entry(1, "일등냥", 1300), entry(2, "이등냥", 1200)] };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })));

    renderPage();

    await waitFor(() => expect(screen.getByText("일등냥")).toBeTruthy());
    expect(screen.getByText("1300")).toBeTruthy();
    expect(screen.getAllByText("5승 2패 0무")).toHaveLength(2);
    expect(screen.getByText("일등냥").closest("a")?.getAttribute("href")).toBe("/players/p1");
  });

  it("[성공] 아직 아무도 없으면 안내 문구를 보여 준다", async () => {
    const body = { page: 1, totalPages: 1, entries: [] };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })));

    renderPage();

    await waitFor(() => expect(screen.getByText(/아직 랭킹에 오른 회원이 없습니다/)).toBeTruthy());
  });

  it("[성공] 다음 쪽 버튼을 누르면 다음 쪽을 요청한다", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      const page = Number(new URL(url, "http://x").searchParams.get("page"));
      return new Response(JSON.stringify({ page, totalPages: 2, entries: [entry(page * 20 - 19, `냥${page}`, 1000)] }), {
        status: 200,
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderPage();
    await waitFor(() => expect(screen.getByText("냥1")).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "다음" }));

    await waitFor(() => expect(screen.getByText("냥2")).toBeTruthy());
    expect(fetchMock).toHaveBeenLastCalledWith("/api/rankings?page=2", expect.anything());
  });
});
