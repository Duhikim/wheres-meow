import type { Socket } from "socket.io-client";
import { create } from "zustand";
import { useMatchStore, type MatchWaiting } from "../match/matchStore";
import { ROOM_GONE_CODES, useRoomStore, type WaitingRoom } from "../room/roomStore";
import { playSound, soundKindOfCells } from "../sound/sound";
import { gameReducer } from "./gameReducer";
import type {
  EndedPayload,
  GameAction,
  GameState,
  RematchCancelReason,
  RematchState,
  RevealedPayload,
  StartedPayload,
  StatePayload,
  TimeoutPayload,
} from "./types";

interface GameStore {
  game: GameState | null;
  lastError: string | null; // 서버 error 이벤트의 code
  connection: "connected" | "reconnecting"; // 소켓이 예기치 않게 끊겨 다시 붙는 중인지
  rematch: RematchState | null;
  dispatch: (action: GameAction) => void;
  setError: (code: string | null) => void;
  markRematchRequested: (gameId: string) => void;
  markRematchDeclined: (gameId: string) => void;
}

function rematchOf(current: RematchState | null, gameId: string): RematchState {
  return current?.gameId === gameId ? current : { gameId, mine: false, theirs: false, cancelled: null };
}

export const useGameStore = create<GameStore>((set) => ({
  game: null,
  lastError: null,
  connection: "connected",
  rematch: null,
  dispatch: (action) => set((state) => ({ game: gameReducer(state.game, action) })),
  setError: (code) => set({ lastError: code }),
  markRematchRequested: (gameId) => set((state) => ({ rematch: { ...rematchOf(state.rematch, gameId), mine: true } })),
  markRematchDeclined: (gameId) =>
    set((state) => ({ rematch: { ...rematchOf(state.rematch, gameId), cancelled: "I_DECLINED" } })),
}));

export function bindGameEvents(socket: Socket): void {
  const { dispatch, setError } = useGameStore.getState();
  const rooms = useRoomStore.getState();
  const match = useMatchStore.getState();
  socket.on("connect", () => {
    useGameStore.setState({ connection: "connected" });
    // 서버는 연결이 끊긴 사람을 대기열에서 뺀다. 기다리던 중이었다면 다시 줄을 선다.
    if (useMatchStore.getState().waiting) socket.emit("match:join");
    // 끊긴 사이 놓친 이벤트가 있을 수 있으므로 진행 중인 대국의 전체 상태를 다시 받는다
    const game = useGameStore.getState().game;
    if (game?.status === "IN_PROGRESS") socket.emit("game:sync", { gameId: game.gameId });
  });
  socket.on("disconnect", (reason: string) => {
    // 직접 끊은 경우(토큰 교체, 세션 만료)는 다시 붙지 않으므로 재연결 표시를 하지 않는다
    if (reason !== "io client disconnect") useGameStore.setState({ connection: "reconnecting" });
  });
  socket.on("room:waiting", (payload: WaitingRoom) => rooms.setWaitingRoom(payload));
  socket.on("room:cancelled", () => rooms.clearWaitingRoom());
  socket.on("match:waiting", (payload: MatchWaiting) => match.setWaiting(payload));
  socket.on("game:started", (payload: StartedPayload) => {
    setError(null);
    rooms.clearWaitingRoom();
    match.clearWaiting();
    useGameStore.setState({ rematch: null });
    dispatch({ type: "started", payload });
  });
  socket.on("game:rematch-requested", ({ gameId }: { gameId: string }) =>
    useGameStore.setState((state) => ({ rematch: { ...rematchOf(state.rematch, gameId), theirs: true } })),
  );
  socket.on("game:rematch-cancelled", ({ gameId, reason }: { gameId: string; reason: RematchCancelReason }) =>
    useGameStore.setState((state) => ({ rematch: { ...rematchOf(state.rematch, gameId), cancelled: reason } })),
  );
  socket.on("game:state", (payload: StatePayload) => dispatch({ type: "state", payload }));
  socket.on("game:revealed", (payload: RevealedPayload) => {
    dispatch({ type: "revealed", payload });
    const kind = soundKindOfCells(payload.cells); // 내 수와 상대 수 모두 소리를 낸다
    if (kind) playSound(kind);
  });
  socket.on("game:timeout", (payload: TimeoutPayload) => dispatch({ type: "timeout", payload }));
  socket.on("game:ended", (payload: EndedPayload) => dispatch({ type: "ended", payload }));
  socket.on("error", (payload: { code: string }) => {
    if (ROOM_GONE_CODES.has(payload.code)) rooms.clearWaitingRoom();
    if (payload.code === "ALREADY_IN_GAME") match.clearWaiting();
    // 재연결 뒤 다시 줄을 섰는데 옛 연결의 대기가 아직 남아 있다. 그대로 기다리면 되므로 오류로 보이지 않는다.
    if (payload.code === "ALREADY_QUEUED" && useMatchStore.getState().waiting) return;
    // 내 재대결 신청을 서버가 거부했다(마감 직후, 상대가 막 떠남). 기다림 표시를 멈춘다.
    const rematch = useGameStore.getState().rematch;
    if (payload.code === "REMATCH_EXPIRED" && rematch && !rematch.cancelled) {
      useGameStore.setState({ rematch: { ...rematch, cancelled: "EXPIRED" } });
    }
    setError(payload.code);
  });
}
