// 서버 Socket.IO 페이로드와 1:1 로 대응한다 (server/.../game/adapter/outbound/socket/payloads.py).

export type SeatIndex = 0 | 1;

export type CellPayload =
  | { x: number; y: number; kind: "number"; n: number }
  | { x: number; y: number; kind: "cat"; seat: SeatIndex };

export interface SeatPayload {
  nickname: string;
  skin: number;
  score: number;
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

export interface EndedPayload {
  gameId: string;
  reason: EndReason;
  winner: SeatIndex | null;
  scores: [number, number];
  cats: [number, number][];
  version: number;
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
  result: { reason: EndReason; winner: SeatIndex | null } | null;
  outOfSync: boolean; // version 이 건너뛰었다. 2단계에서 game:sync 로 복구한다
}

export type GameAction =
  | { type: "started"; payload: StartedPayload }
  | { type: "revealed"; payload: RevealedPayload }
  | { type: "timeout"; payload: TimeoutPayload }
  | { type: "ended"; payload: EndedPayload };

export const cellKey = (x: number, y: number) => `${x},${y}`;
