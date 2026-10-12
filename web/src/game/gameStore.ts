import type { Socket } from "socket.io-client";
import { create } from "zustand";
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
  socket.on("game:started", (payload: StartedPayload) => {
    setError(null);
    dispatch({ type: "started", payload });
  });
  socket.on("game:revealed", (payload: RevealedPayload) => dispatch({ type: "revealed", payload }));
  socket.on("game:timeout", (payload: TimeoutPayload) => dispatch({ type: "timeout", payload }));
  socket.on("game:ended", (payload: EndedPayload) => dispatch({ type: "ended", payload }));
  socket.on("error", (payload: { code: string }) => setError(payload.code));
}
