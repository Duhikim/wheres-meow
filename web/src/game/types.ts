// 서버 Socket.IO 페이로드와 1:1 로 대응한다 (server/.../game/adapter/outbound/socket/payloads.py).

export type SeatIndex = 0 | 1;

export type CellPayload =
  | { x: number; y: number; kind: "number"; n: number }
  | { x: number; y: number; kind: "cat"; seat: SeatIndex };

export interface SeatPayload {
  nickname: string;
  skin: number;
  score: number;
  isBot?: boolean; // 컴퓨터 대전의 봇 좌석
}

export interface StartedPayload {
  gameId: string;
  mode: "INVITE" | "MATCH" | "BOT";
  mySeat: SeatIndex;
  seats: [SeatPayload, SeatPayload];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
  cells: CellPayload[];
}

export interface RevealedPayload {
  gameId: string;
  seat: SeatIndex;
  cells: CellPayload[];
  scores: [number, number];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
}

export interface TimeoutPayload {
  gameId: string;
  seat: SeatIndex;
  scores: [number, number];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
}

export type EndReason = "ALL_FOUND" | "FORFEIT" | "AUTO_FORFEIT";

export interface RatingChange {
  before: number;
  after: number;
}

/** 좌석 순서대로의 레이팅 변화. 사람 간 대국이 아니거나 서버가 결과를 저장하지 못했으면 null. */
export type RatingChanges = [RatingChange, RatingChange] | null;

export interface GameResult {
  reason: EndReason;
  winner: SeatIndex | null;
  ratingChanges: RatingChanges;
}

export interface EndedPayload {
  gameId: string;
  reason: EndReason;
  winner: SeatIndex | null;
  scores: [number, number];
  cats: [number, number][];
  ratingChanges: RatingChanges;
  version: number;
}

/** game:sync 응답. 끝난 대국이면 result 와 cats 가 있다. */
export interface StatePayload extends StartedPayload {
  status: "IN_PROGRESS" | "FINISHED";
  result: GameResult | null;
  timeouts: [number, number];
  cats?: [number, number][];
}

// 화면 상태

export type Cell =
  | { kind: "number"; n: number }
  | { kind: "cat"; seat: SeatIndex | null }; // seat null = 끝난 뒤 공개된, 아무도 못 찾은 고양이

export interface GameState {
  gameId: string;
  mode: StartedPayload["mode"];
  mySeat: SeatIndex;
  seats: [SeatPayload, SeatPayload];
  currentSeat: SeatIndex;
  turnDeadline: number | null;
  version: number;
  cells: Record<string, Cell>;
  status: "IN_PROGRESS" | "FINISHED";
  result: GameResult | null;
  outOfSync: boolean; // version 이 건너뛰었다. 2단계에서 game:sync 로 복구한다
}

export type GameAction =
  | { type: "started"; payload: StartedPayload }
  | { type: "state"; payload: StatePayload }
  | { type: "revealed"; payload: RevealedPayload }
  | { type: "timeout"; payload: TimeoutPayload }
  | { type: "ended"; payload: EndedPayload };

export const cellKey = (x: number, y: number) => `${x},${y}`;
