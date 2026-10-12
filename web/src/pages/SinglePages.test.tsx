import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../session/sessionStore";
import { newGame, reveal, seededRandom } from "../single/engine";
import { SinglePlayPage, soundOfStep } from "./SinglePlayPage";
import { SingleSelectPage } from "./SingleSelectPage";

const player = { id: "p1", kind: "GUEST" as const, nickname: "연습냥", skin1p: 16, skin2p: 17 };
const records = [
  { difficulty: "BEGINNER", bestMs: 41_234, clears: 3 },
  { difficulty: "INTERMEDIATE", bestMs: null, clears: 0 },
  { difficulty: "EXPERT", bestMs: null, clears: 0 },
];

beforeEach(() => useSession.getState().setSession("token", player));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/single" element={<SingleSelectPage />} />
        <Route path="/single/:difficulty" element={<SinglePlayPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

const cell = (x: number, y: number) => screen.getByRole("button", { name: `${x},${y}` });

describe("SingleSelectPage", () => {
  it("[성공] 세 난이도와 내 최고 기록을 보여 주고 판으로 연결한다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(records), { status: 200 })));

    renderAt("/single");

    await waitFor(() => expect(screen.getByText("최고 41.2초")).toBeTruthy());
    expect(screen.getAllByText("기록 없음")).toHaveLength(2);
    expect(screen.getByRole("link", { name: /초급/ }).getAttribute("href")).toBe("/single/BEGINNER");
    expect(screen.getByRole("link", { name: /고급/ }).getAttribute("href")).toBe("/single/EXPERT");
  });
});

describe("SinglePlayPage", () => {
  it("[성공] 난이도 크기의 판을 그린다", () => {
    renderAt("/single/EXPERT");

    expect(screen.getAllByRole("button", { name: /^\d+,\d+$/ })).toHaveLength(12 * 16);
    expect(screen.getByText("🐱 40")).toBeTruthy();
  });

  it("[성공] 깃발 모드에서 누르면 깃발을 꽂고 남은 고양이 수가 줄어든다", () => {
    renderAt("/single/BEGINNER?seed=3");

    fireEvent.click(screen.getByRole("button", { name: /깃발 모드/ }));
    fireEvent.click(cell(0, 0));

    expect(cell(0, 0).textContent).toContain("🚩");
    expect(screen.getByText("🐱 9")).toBeTruthy();
  });

  it("[성공] 고양이가 아닌 칸을 모두 열면 성공하고 클리어 시간을 서버에 보낸다", async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify({ difficulty: "BEGINNER", bestMs: 5000, newBest: true, clears: 1 }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderAt("/single/BEGINNER?seed=3");
    const cats = reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(3)).cats!;

    fireEvent.click(cell(4, 4));
    for (let y = 0; y < 9; y++) {
      for (let x = 0; x < 9; x++) {
        const button = cell(x, y);
        if (!cats.has(`${x},${y}`) && button.className.includes("closed")) fireEvent.click(button);
      }
    }

    await waitFor(() => expect(screen.getByText("성공!")).toBeTruthy());
    expect(screen.getByText("최고 기록을 새로 세웠습니다!")).toBeTruthy();
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/players/me/single-records");
    expect(JSON.parse(init.body as string)).toMatchObject({ difficulty: "BEGINNER" });
  });

  it("[실패] 고양이를 누르면 실패하고 기록을 보내지 않는다", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderAt("/single/BEGINNER?seed=3");
    const cats = [...reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(3)).cats!];
    fireEvent.click(cell(4, 4));

    const [x, y] = cats[0].split(",").map(Number);
    fireEvent.click(cell(x, y));

    expect(screen.getByText("고양이를 건드렸습니다")).toBeTruthy();
    expect(cell(x, y).className).toContain("exploded");
    expect(fetchMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "다시 하기" }));
    expect(screen.queryByText("고양이를 건드렸습니다")).toBeNull();
  });

  it("[성공] 길게 누르면 깃발을 꽂는다", () => {
    vi.useFakeTimers();
    try {
      renderAt("/single/BEGINNER?seed=3");

      fireEvent.pointerDown(cell(2, 2));
      act(() => vi.advanceTimersByTime(500));
      fireEvent.pointerUp(cell(2, 2));
      fireEvent.click(cell(2, 2)); // 길게 누른 뒤 따라오는 클릭은 무시한다

      expect(cell(2, 2).textContent).toContain("🚩");
      expect(cell(2, 2).className).toContain("closed");
    } finally {
      vi.useRealTimers();
    }
  });

  it("[실패] 알 수 없는 난이도면 선택 화면으로 돌려보낸다", () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(records), { status: 200 })));

    renderAt("/single/IMPOSSIBLE");

    expect(screen.getByText("혼자 연습")).toBeTruthy();
  });
});

describe("soundOfStep", () => {
  const base = reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(3));
  const cats = [...base.cats!];

  it("[성공] 고양이를 건드리면 고양이 소리다", () => {
    const [x, y] = cats[0].split(",").map(Number);
    expect(soundOfStep(base, reveal(base, x, y, 1, seededRandom(3)))).toBe("cat");
  });

  it("[성공] 숫자 칸이 새로 열리면 발자국 소리고, 빈 흙만 열리면 흙 소리다", () => {
    const fresh = newGame("BEGINNER");
    const first = reveal(fresh, 4, 4, 0, seededRandom(3));
    const hasNumber = [...first.opened.values()].some((n) => n > 0);
    expect(soundOfStep(fresh, first)).toBe(hasNumber ? "paw" : "dirt");
    expect(soundOfStep(first, { ...first, opened: new Map([...first.opened, ["99,99", 0]]) })).toBe("dirt");
  });
});
