import type { GameState } from "./types";

export interface MyRatingChange {
  before: number;
  after: number;
  delta: number;
}

/** 끝난 대국에서 내 레이팅 변화. 레이팅이 바뀌지 않는 대국(컴퓨터 대전)이거나 저장에 실패했으면 null. */
export function myRatingChange(game: GameState): MyRatingChange | null {
  const change = game.result?.ratingChanges?.[game.mySeat];
  return change ? { ...change, delta: change.after - change.before } : null;
}

export function formatDelta(delta: number): string {
  if (delta === 0) return "±0";
  return delta > 0 ? `+${delta}` : `${delta}`;
}
