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
  move: { x: number; y: number }; // 누른 칸. 연쇄로 여러 칸이 열려도 이 칸 하나다
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

/** 서버가 보내는 취소 사유 네 가지와, 내가 거절했음을 나타내는 화면 전용 I_DECLINED. */
export type RematchCancelReason = "DECLINED" | "EXPIRED" | "LEFT" | "UNAVAILABLE" | "I_DECLINED";

/** 끝난 대국 하나의 재대결 협상 상태. */
export interface RematchState {
  gameId: string;
  mine: boolean; // 내가 신청했다
  theirs: boolean; // 상대가 신청했다
  cancelled: RematchCancelReason | null;
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
  lastMove: LastMove | null; // 가장 최근에 칸을 연 수. 상대 수 이펙트에 쓴다
}

export interface LastMove {
  seat: SeatIndex;
  x: number;
  y: number;
  version: number; // 같은 칸을 다시 눌러도 이펙트를 새로 틀기 위한 구분값
}

export type GameAction =
  | { type: "started"; payload: StartedPayload }
  | { type: "state"; payload: StatePayload }
  | { type: "revealed"; payload: RevealedPayload }
  | { type: "timeout"; payload: TimeoutPayload }
  | { type: "ended"; payload: EndedPayload };

export const cellKey = (x: number, y: number) => `${x},${y}`;
