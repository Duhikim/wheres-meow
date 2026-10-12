import type { Socket } from "socket.io-client";
import { create } from "zustand";
import { ROOM_GONE_CODES, useRoomStore, type WaitingRoom } from "../room/roomStore";
import { gameReducer } from "./gameReducer";
import type {
  EndedPayload,
  GameAction,
  GameState,
  RevealedPayload,
  StartedPayload,
  StatePayload,
  TimeoutPayload,
} from "./types";

interface GameStore {
  game: GameState | null;
  lastError: string | null; // 서버 error 이벤트의 code
  connection: "connected" | "reconnecting"; // 소켓이 예기치 않게 끊겨 다시 붙는 중인지
  dispatch: (action: GameAction) => void;
  setError: (code: string | null) => void;
}

export const useGameStore = create<GameStore>((set) => ({
  game: null,
  lastError: null,
  connection: "connected",
  dispatch: (action) => set((state) => ({ game: gameReducer(state.game, action) })),
  setError: (code) => set({ lastError: code }),
}));

export function bindGameEvents(socket: Socket): void {
  const { dispatch, setError } = useGameStore.getState();
  const rooms = useRoomStore.getState();
  socket.on("connect", () => {
    useGameStore.setState({ connection: "connected" });
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
  socket.on("game:started", (payload: StartedPayload) => {
    setError(null);
    rooms.clearWaitingRoom();
    dispatch({ type: "started", payload });
  });
  socket.on("game:state", (payload: StatePayload) => dispatch({ type: "state", payload }));
  socket.on("game:revealed", (payload: RevealedPayload) => dispatch({ type: "revealed", payload }));
  socket.on("game:timeout", (payload: TimeoutPayload) => dispatch({ type: "timeout", payload }));
  socket.on("game:ended", (payload: EndedPayload) => dispatch({ type: "ended", payload }));
  socket.on("error", (payload: { code: string }) => {
    if (ROOM_GONE_CODES.has(payload.code)) rooms.clearWaitingRoom();
    setError(payload.code);
  });
}
