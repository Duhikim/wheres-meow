import { describe, expect, it } from "vitest";
import {
  chord,
  elapsedMs,
  LEVELS,
  newGame,
  remainingCats,
  reveal,
  seededRandom,
  toggleFlag,
  withCats,
  type SingleState,
} from "./engine";

/** 4×4 판에 고양이를 직접 놓은 진행 중 상태(첫 칸 배치 규칙을 건너뛴다). */
function fixed(cats: [number, number][]): SingleState {
  return withCats({ ...newGame("BEGINNER"), width: 4, height: 4, catCount: cats.length }, cats, 0);
}

describe("LEVELS", () => {
  it("[성공] 난이도 세 가지의 판 크기와 고양이 수", () => {
    expect(LEVELS.BEGINNER).toMatchObject({ width: 9, height: 9, cats: 10 });
    expect(LEVELS.INTERMEDIATE).toMatchObject({ width: 12, height: 12, cats: 25 });
    expect(LEVELS.EXPERT).toMatchObject({ width: 12, height: 16, cats: 40 });
  });
});

describe("reveal", () => {
  describe("첫 칸", () => {
    it("[성공] 첫 칸과 주변 8칸에는 고양이를 두지 않고, 정해진 수만큼 배치한다", () => {
      for (let seed = 1; seed <= 30; seed++) {
        const state = reveal(newGame("EXPERT"), 5, 7, 1000, seededRandom(seed));

        expect(state.cats!.size).toBe(40);
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) expect(state.cats!.has(`${5 + dx},${7 + dy}`)).toBe(false);
        }
        expect(state.status).not.toBe("LOST");
      }
    });

    it("[성공] 첫 칸을 누른 시각부터 시간을 잰다", () => {
      const state = reveal(newGame("BEGINNER"), 0, 0, 5000, seededRandom(1));

      expect(state.startedAt).toBe(5000);
      expect(elapsedMs(state, 8500)).toBe(3500);
    });

    it("[성공] 같은 시드면 같은 판이 나온다", () => {
      const a = reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(7));
      const b = reveal(newGame("BEGINNER"), 4, 4, 0, seededRandom(7));

      expect([...a.cats!].sort()).toEqual([...b.cats!].sort());
    });
  });

  describe("열기", () => {
    it("[성공] 숫자 칸은 그 칸만 연다", () => {
      const state = reveal(fixed([[0, 0]]), 1, 0, 1, seededRandom(1));

      expect(state.opened.get("1,0")).toBe(1);
      expect(state.opened.size).toBe(1);
    });

    it("[성공] 빈 칸은 이어진 빈 칸과 그 경계의 숫자까지 한꺼번에 연다", () => {
      const state = reveal(fixed([[0, 0]]), 3, 3, 1, seededRandom(1));

      expect(state.opened.size).toBe(15); // 고양이 칸 하나를 뺀 전부
      expect(state.status).toBe("WON");
    });

    it("[실패] 고양이를 누르면 지고 그 칸을 기록한다", () => {
      const state = reveal(fixed([[0, 0], [3, 3]]), 0, 0, 1, seededRandom(1));

      expect(state.status).toBe("LOST");
      expect(state.explodedKey).toBe("0,0");
      expect(state.endedAt).toBe(1);
    });

    it("[실패] 깃발 꽂은 칸은 열리지 않는다", () => {
      const flagged = toggleFlag(fixed([[0, 0]]), 0, 0);

      expect(reveal(flagged, 0, 0, 1, seededRandom(1))).toBe(flagged);
    });

    it("[실패] 끝난 판에서는 아무 일도 일어나지 않는다", () => {
      const lost = reveal(fixed([[0, 0], [3, 3]]), 0, 0, 1, seededRandom(1));

      expect(reveal(lost, 2, 2, 2, seededRandom(1))).toBe(lost);
    });

    it("[성공] 고양이가 아닌 칸을 모두 열면 이기고 끝난 시각을 남긴다", () => {
      let state = fixed([[0, 0], [3, 3]]);
      for (let y = 0; y < 4; y++) {
        for (let x = 0; x < 4; x++) {
          if ((x === 0 && y === 0) || (x === 3 && y === 3)) continue;
          state = reveal(state, x, y, 10 + x + y, seededRandom(1));
        }
      }

      expect(state.status).toBe("WON");
      expect(state.endedAt).not.toBeNull();
    });
  });
});

describe("toggleFlag", () => {
  it("[성공] 닫힌 칸에 깃발을 꽂고 다시 누르면 뽑는다", () => {
    const flagged = toggleFlag(fixed([[0, 0]]), 2, 2);
    expect(flagged.flags.has("2,2")).toBe(true);
    expect(remainingCats(flagged)).toBe(0);

    expect(toggleFlag(flagged, 2, 2).flags.has("2,2")).toBe(false);
  });

  it("[실패] 열린 칸에는 깃발을 꽂지 않는다", () => {
    const opened = reveal(fixed([[0, 0]]), 1, 0, 1, seededRandom(1));

    expect(toggleFlag(opened, 1, 0)).toBe(opened);
  });

  it("[성공] 첫 칸을 열기 전에도 깃발을 꽂을 수 있고, 첫 배치는 깃발 칸도 비워 두지 않는다(규칙 단순화)", () => {
    const state = toggleFlag(newGame("BEGINNER"), 8, 8);

    expect(state.flags.has("8,8")).toBe(true);
    expect(remainingCats(state)).toBe(9);
  });
});

describe("chord", () => {
  it("[성공] 숫자만큼 깃발이 있으면 나머지 주변 칸을 연다", () => {
    let state = fixed([[0, 0], [3, 3]]);
    state = reveal(state, 1, 1, 1, seededRandom(1)); // 주변에 고양이 1마리(0,0)
    state = toggleFlag(state, 0, 0);

    state = chord(state, 1, 1, 2);

    for (const key of ["0,1", "1,0", "2,0", "0,2", "2,2"]) expect(state.opened.has(key)).toBe(true);
    expect(state.status).not.toBe("LOST");
  });

  it("[실패] 깃발 수가 숫자와 다르면 아무것도 열지 않는다", () => {
    const state = reveal(fixed([[0, 0], [3, 3]]), 1, 1, 1, seededRandom(1));

    expect(chord(state, 1, 1, 2)).toBe(state);
  });

  it("[실패] 깃발을 잘못 꽂고 코딩하면 고양이를 열어 진다", () => {
    let state = reveal(fixed([[0, 0], [3, 3]]), 1, 1, 1, seededRandom(1));
    state = toggleFlag(state, 1, 0); // 틀린 깃발

    state = chord(state, 1, 1, 2);

    expect(state.status).toBe("LOST");
    expect(state.explodedKey).toBe("0,0");
  });
});
