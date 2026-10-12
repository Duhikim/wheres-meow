import type { Socket } from "socket.io-client";
import { create } from "zustand";
import { ROOM_GONE_CODES, useRoomStore, type WaitingRoom } from "../room/roomStore";
import { gameReducer } from "./gameReducer";
import type { EndedPayload, GameAction, GameState, RevealedPayload, StartedPayload, TimeoutPayload } from "./types";

interface GameStore {
  game: GameState | null;
  lastError: string | null; // 서버 error 이벤트의 code
  dispatch: (action: GameAction) => void;
  setError: (code: string | null) => void;
}

export const useGameStore = create<GameStore>((set) => ({
  game: null,
  lastError: null,
  dispatch: (action) => set((state) => ({ game: gameReducer(state.game, action) })),
  setError: (code) => set({ lastError: code }),
}));

export function bindGameEvents(socket: Socket): void {
  const { dispatch, setError } = useGameStore.getState();
  const rooms = useRoomStore.getState();
  socket.on("room:waiting", (payload: WaitingRoom) => rooms.setWaitingRoom(payload));
  socket.on("room:cancelled", () => rooms.clearWaitingRoom());
  socket.on("game:started", (payload: StartedPayload) => {
    setError(null);
    rooms.clearWaitingRoom();
    dispatch({ type: "started", payload });
  });
  socket.on("game:revealed", (payload: RevealedPayload) => dispatch({ type: "revealed", payload }));
  socket.on("game:timeout", (payload: TimeoutPayload) => dispatch({ type: "timeout", payload }));
  socket.on("game:ended", (payload: EndedPayload) => dispatch({ type: "ended", payload }));
  socket.on("error", (payload: { code: string }) => {
    if (ROOM_GONE_CODES.has(payload.code)) rooms.clearWaitingRoom();
    setError(payload.code);
  });
}
