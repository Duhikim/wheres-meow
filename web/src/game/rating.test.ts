import { describe, expect, it } from "vitest";
import { formatDelta, myRatingChange } from "./rating";
import type { GameState, RatingChange } from "./types";

function finished(ratingChanges: [RatingChange, RatingChange] | null, mySeat: 0 | 1 = 0) {
  return {
    mySeat,
    result: { reason: "FORFEIT", winner: 0, ratingChanges },
  } as unknown as GameState;
}

describe("myRatingChange", () => {
  it("[성공] 내 좌석의 레이팅 변화와 차이를 돌려준다", () => {
    const game = finished([{ before: 1000, after: 984 }, { before: 1000, after: 1016 }], 1);

    expect(myRatingChange(game)).toEqual({ before: 1000, after: 1016, delta: 16 });
  });

  it("[실패] 레이팅 변화가 없으면(컴퓨터 대전, 저장 실패) null", () => {
    expect(myRatingChange(finished(null))).toBeNull();
  });
});

describe("formatDelta", () => {
  it("[성공] 오르면 +, 내리면 -, 같으면 ±0 을 붙인다", () => {
    expect(formatDelta(16)).toBe("+16");
    expect(formatDelta(-7)).toBe("-7");
    expect(formatDelta(0)).toBe("±0");
  });
});
