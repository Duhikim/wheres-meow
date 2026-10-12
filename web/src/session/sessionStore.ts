import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, ApiError, setUnauthorizedHandler } from "../api/http";

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

// 서버 재시작 등으로 토큰이 무효가 되면 어느 화면에서든 세션을 지워 닉네임 입력으로 돌아간다
setUnauthorizedHandler(() => useSession.getState().clear());

/** 내 고양이 1P·2P 를 서버에 저장하고 세션의 내 정보를 갱신한다. */
export async function saveSkins(skin1p: number, skin2p: number): Promise<void> {
  const { token, setSession } = useSession.getState();
  if (!token) throw new Error("로그인 세션이 없습니다");
  const player = await api<Player>("/api/players/me/skins", { method: "PUT", body: { skin1p, skin2p }, token });
  setSession(token, player);
}

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
    // 서버는 조회할 때마다 새 토큰을 준다. 저장해 두면 쓰는 동안 만료일이 계속 30일 뒤로 밀린다.
    const { token: renewed, ...player } = await api<Player & { token: string }>("/api/players/me", { token });
    useSession.getState().setSession(renewed, player);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) clear();
    else throw error;
  }
}
