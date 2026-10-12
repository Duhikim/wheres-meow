/**
 * 혼자 연습(클래식 지뢰찾기) 규칙. 화면과 무관한 순수 함수이며, 상태를 바꾸지 않고 새 상태를 돌려준다.
 * 아무 일도 일어나지 않는 동작(끝난 판, 깃발 칸 열기 등)은 같은 상태 객체를 그대로 돌려준다.
 */

export type Difficulty = "BEGINNER" | "INTERMEDIATE" | "EXPERT";

export const LEVELS: Record<Difficulty, { width: number; height: number; cats: number; label: string }> = {
  BEGINNER: { width: 9, height: 9, cats: 10, label: "초급" },
  INTERMEDIATE: { width: 12, height: 12, cats: 25, label: "중급" },
  EXPERT: { width: 12, height: 16, cats: 40, label: "고급" },
};

export const DIFFICULTIES = Object.keys(LEVELS) as Difficulty[];

export type SingleStatus = "READY" | "PLAYING" | "WON" | "LOST";

export interface SingleState {
  difficulty: Difficulty;
  width: number;
  height: number;
  catCount: number;
  cats: Set<string> | null; // 첫 칸을 열 때 배치한다
  opened: Map<string, number>; // 열린 칸 → 주변 고양이 수
  flags: Set<string>;
  status: SingleStatus;
  explodedKey: string | null; // 지게 만든 고양이 칸
  startedAt: number | null;
  endedAt: number | null;
}

export type Random = () => number; // [0, 1)

const key = (x: number, y: number) => `${x},${y}`;

export function newGame(difficulty: Difficulty): SingleState {
  const level = LEVELS[difficulty];
  return {
    difficulty,
    width: level.width,
    height: level.height,
    catCount: level.cats,
    cats: null,
    opened: new Map(),
    flags: new Set(),
    status: "READY",
    explodedKey: null,
    startedAt: null,
    endedAt: null,
  };
}

/** 고양이를 정해진 자리에 놓고 시작한 상태(첫 칸 배치와 테스트에서 쓴다). */
export function withCats(state: SingleState, cats: [number, number][], now: number): SingleState {
  return { ...state, cats: new Set(cats.map(([x, y]) => key(x, y))), status: "PLAYING", startedAt: now };
}

/** 같은 시드면 같은 수열을 내는 난수(mulberry32). E2E 가 판을 고정할 때 쓴다. */
export function seededRandom(seed: number): Random {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function neighbors(state: SingleState, x: number, y: number): [number, number][] {
  const result: [number, number][] = [];
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx;
      const ny = y + dy;
      if ((dx || dy) && nx >= 0 && ny >= 0 && nx < state.width && ny < state.height) result.push([nx, ny]);
    }
  }
  return result;
}

/** 첫 칸과 그 주변 8칸을 피해 고양이를 무작위로 놓는다. */
function placeCats(state: SingleState, x: number, y: number, random: Random): [number, number][] {
  const safe = new Set([key(x, y), ...neighbors(state, x, y).map(([nx, ny]) => key(nx, ny))]);
  const candidates: [number, number][] = [];
  for (let cy = 0; cy < state.height; cy++) {
    for (let cx = 0; cx < state.width; cx++) if (!safe.has(key(cx, cy))) candidates.push([cx, cy]);
  }
  if (candidates.length < state.catCount) throw new Error(`고양이 ${state.catCount}마리를 놓을 칸이 부족합니다`);
  for (let i = candidates.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
  }
  return candidates.slice(0, state.catCount);
}

function countAround(state: SingleState, x: number, y: number): number {
  return neighbors(state, x, y).filter(([nx, ny]) => state.cats!.has(key(nx, ny))).length;
}

/** 여러 칸을 차례로 연다. 빈 칸(0)은 이어진 영역을 넓혀 연다. 고양이를 열면 그 자리에서 진다. */
function openCells(state: SingleState, starts: [number, number][], now: number): SingleState {
  const opened = new Map(state.opened);
  const stack = [...starts];
  while (stack.length) {
    const [x, y] = stack.pop()!;
    const k = key(x, y);
    if (opened.has(k) || state.flags.has(k)) continue;
    if (state.cats!.has(k)) return { ...state, opened, status: "LOST", explodedKey: k, endedAt: now };
    const n = countAround(state, x, y);
    opened.set(k, n);
    if (n === 0) stack.push(...neighbors(state, x, y));
  }
  const won = opened.size === state.width * state.height - state.catCount;
  return { ...state, opened, status: won ? "WON" : "PLAYING", endedAt: won ? now : null };
}

export function reveal(state: SingleState, x: number, y: number, now: number, random: Random): SingleState {
  const k = key(x, y);
  if (state.status === "WON" || state.status === "LOST" || state.flags.has(k) || state.opened.has(k)) return state;
  const playing = state.status === "READY" ? withCats(state, placeCats(state, x, y, random), now) : state;
  return openCells(playing, [[x, y]], now);
}

export function toggleFlag(state: SingleState, x: number, y: number): SingleState {
  const k = key(x, y);
  if (state.status === "WON" || state.status === "LOST" || state.opened.has(k)) return state;
  const flags = new Set(state.flags);
  if (flags.has(k)) flags.delete(k);
  else flags.add(k);
  return { ...state, flags };
}

/** 열린 숫자 칸 주변의 깃발 수가 그 숫자와 같으면, 깃발이 없는 주변 칸을 모두 연다. */
export function chord(state: SingleState, x: number, y: number, now: number): SingleState {
  const n = state.opened.get(key(x, y));
  if (state.status !== "PLAYING" || n === undefined || n === 0) return state;
  const around = neighbors(state, x, y);
  const flagged = around.filter(([nx, ny]) => state.flags.has(key(nx, ny))).length;
  const closed = around.filter(([nx, ny]) => !state.flags.has(key(nx, ny)) && !state.opened.has(key(nx, ny)));
  if (flagged !== n || closed.length === 0) return state;
  return openCells(state, closed, now);
}

export function remainingCats(state: SingleState): number {
  return state.catCount - state.flags.size;
}

export function elapsedMs(state: SingleState, now: number): number {
  if (state.startedAt === null) return 0;
  return (state.endedAt ?? now) - state.startedAt;
}
