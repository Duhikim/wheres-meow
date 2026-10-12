import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, ApiError } from "../api/http";

export interface Player {
  id: string;
  kind: "MEMBER" | "GUEST";
  nickname: string;
  skin1p: number;
  skin2p: number;
}

interface SessionState {
  token: string | null;
  player: Player | null;
  setSession: (token: string, player: Player) => void;
  clear: () => void;
}

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      token: null,
      player: null,
      setSession: (token, player) => set({ token, player }),
      clear: () => set({ token: null, player: null }),
    }),
    { name: "wheresmeow-session" },
  ),
);

export async function createGuest(nickname: string): Promise<void> {
  const result = await api<{ token: string; player: Player }>("/api/guests", {
    method: "POST",
    body: { nickname },
  });
  useSession.getState().setSession(result.token, result.player);
}

/** 저장된 토큰이 아직 유효한지 확인한다. 서버가 거부하면(재시작 등) 세션을 지운다. */
export async function verifySession(): Promise<void> {
  const { token, clear } = useSession.getState();
  if (!token) return;
  try {
    await api<Player>("/api/players/me", { token });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) clear();
    else throw error;
  }
}
