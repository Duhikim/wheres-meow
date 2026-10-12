import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { GameState, RematchState } from "../game/types";
import { ResultCard } from "./ResultCard";

const game = {
  gameId: "g1",
  mode: "INVITE",
  mySeat: 0,
  seats: [
    { nickname: "나냥", skin: 16, score: 14 },
    { nickname: "너냥", skin: 17, score: 11 },
  ],
  status: "FINISHED",
  result: { reason: "ALL_FOUND", winner: 0, ratingChanges: [{ before: 1000, after: 1016 }, { before: 1000, after: 984 }] },
} as unknown as GameState;

const onRequest = vi.fn();
const onDecline = vi.fn();
const onLeave = vi.fn();

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function renderCard(rematch: RematchState | null, g: GameState = game) {
  render(
    <MemoryRouter>
      <ResultCard game={g} rematch={rematch} onRequestRematch={onRequest} onDeclineRematch={onDecline} onLeave={onLeave} />
    </MemoryRouter>,
  );
}

describe("ResultCard", () => {
  it("[성공] 승패, 점수, 레이팅 변화를 보여 준다", () => {
    renderCard(null);

    expect(screen.getByText("승리!")).toBeTruthy();
    expect(screen.getByText("(+16)")).toBeTruthy();
  });

  it("[성공] 재대결 신청을 누르면 신청한다", () => {
    renderCard(null);

    fireEvent.click(screen.getByRole("button", { name: "재대결 신청" }));

    expect(onRequest).toHaveBeenCalled();
  });

  it("[성공] 내가 신청했으면 상대를 기다린다는 문구와 함께 버튼을 끈다", () => {
    renderCard({ gameId: "g1", mine: true, theirs: false, cancelled: null });

    expect(screen.getByText(/상대의 응답을 기다리는 중/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "재대결 신청" })).toBeNull();
  });

  it("[성공] 상대가 신청했으면 수락·거절 버튼을 보여 준다", () => {
    renderCard({ gameId: "g1", mine: false, theirs: true, cancelled: null });

    fireEvent.click(screen.getByRole("button", { name: "수락" }));
    fireEvent.click(screen.getByRole("button", { name: "거절" }));

    expect(onRequest).toHaveBeenCalled();
    expect(onDecline).toHaveBeenCalled();
  });

  it("[실패] 취소되었으면 사유를 보여 주고 다시 신청할 수 없다", () => {
    renderCard({ gameId: "g1", mine: true, theirs: false, cancelled: "LEFT" });

    expect(screen.getByText("상대가 결과 화면을 떠났습니다.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "재대결 신청" })).toBeNull();
  });

  it("[성공] 로비로를 누르면 결과 화면을 떠난다고 알린다", () => {
    renderCard(null);

    fireEvent.click(screen.getByRole("link", { name: "로비로" }));

    expect(onLeave).toHaveBeenCalled();
  });

  it("[성공] 다른 대국의 재대결 상태는 무시한다", () => {
    renderCard({ gameId: "old", mine: false, theirs: true, cancelled: null });

    expect(screen.queryByRole("button", { name: "수락" })).toBeNull();
    expect(screen.getByRole("button", { name: "재대결 신청" })).toBeTruthy();
  });

  it("[성공] 내가 거절했으면 거절했다는 문구만 보여 준다", () => {
    renderCard({ gameId: "g1", mine: false, theirs: true, cancelled: "I_DECLINED" });

    expect(screen.getByText("재대결을 거절했습니다.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "수락" })).toBeNull();
  });
});
