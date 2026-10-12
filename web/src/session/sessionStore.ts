import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, ApiError, setRefreshHandler, setUnauthorizedHandler } from "../api/http";

export interface Player {
  id: string;
  kind: "MEMBER" | "GUEST";
  nickname: string;
  skin1p: number;
  skin2p: number;
  needsNickname?: boolean; // 소셜 로그인으로 막 가입해 임시 닉네임을 쓰는 중
}

interface AuthResponse {
  token: string;
  player: Player;
}

interface SessionState {
  token: string | null;
  player: Player | null;
  setSession: (token: string, player: Player) => void;
  setPlayer: (player: Player) => void;
  clear: () => void;
}

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      token: null,
      player: null,
      setSession: (token, player) => set({ token, player }),
      setPlayer: (player) => set({ player }),
      clear: () => set({ token: null, player: null }),
    }),
    {
      name: "wheresmeow-session",
      // 회원의 액세스 토큰은 메모리에만 둔다(스펙 4.4). 새로고침하면 리프레시 쿠키로 다시 받는다.
      partialize: (state) => ({
        player: state.player,
        token: state.player?.kind === "GUEST" ? state.token : null,
      }),
    },
  ),
);

let refreshInFlight: Promise<string | null> | null = null;

/**
 * 리프레시 쿠키로 새 액세스 토큰을 받는다. 실패하면 세션을 지우고 null.
 * 리프레시 토큰은 한 번 쓰면 폐기되므로, 동시에 여러 곳에서 불러도 요청은 하나만 보내고 결과를 나눠 갖는다.
 * (같은 토큰으로 두 번 보내면 서버는 재사용으로 보고 그 회원의 토큰을 모두 끊는다.)
 */
export function refreshMemberSession(): Promise<string | null> {
  refreshInFlight ??= requestRefresh().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function requestRefresh(): Promise<string | null> {
  try {
    const result = await api<AuthResponse>("/api/auth/refresh", { method: "POST" });
    useSession.getState().setSession(result.token, result.player);
    return result.token;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      useSession.getState().clear();
      return null;
    }
    throw error;
  }
}

// 서버 재시작 등으로 토큰이 무효가 되면 어느 화면에서든 세션을 지워 닉네임 입력으로 돌아간다
setUnauthorizedHandler(() => useSession.getState().clear());
// 회원 요청이 401 이면 리프레시 쿠키로 한 번 새 토큰을 받는다. 게스트는 받을 방법이 없다.
setRefreshHandler(async () => (useSession.getState().player?.kind === "MEMBER" ? refreshMemberSession() : null));

/** 내 고양이 1P·2P 를 서버에 저장하고 세션의 내 정보를 갱신한다. */
export async function saveSkins(skin1p: number, skin2p: number): Promise<void> {
  const { token } = useSession.getState();
  if (!token) throw new Error("로그인 세션이 없습니다");
  const player = await api<Player>("/api/players/me/skins", { method: "PUT", body: { skin1p, skin2p }, token });
  useSession.getState().setPlayer(player);
}

export async function saveNickname(nickname: string): Promise<void> {
  const { token } = useSession.getState();
  if (!token) throw new Error("로그인 세션이 없습니다");
  const player = await api<Player>("/api/players/me/nickname", { method: "PUT", body: { nickname }, token });
  useSession.getState().setPlayer(player);
}

export async function createGuest(nickname: string): Promise<void> {
  const result = await api<AuthResponse>("/api/guests", { method: "POST", body: { nickname } });
  useSession.getState().setSession(result.token, result.player);
}

export async function signup(username: string, password: string, nickname: string): Promise<void> {
  const result = await api<AuthResponse>("/api/auth/signup", { method: "POST", body: { username, password, nickname } });
  useSession.getState().setSession(result.token, result.player);
}

export async function login(username: string, password: string): Promise<void> {
  const result = await api<AuthResponse>("/api/auth/login", { method: "POST", body: { username, password } });
  useSession.getState().setSession(result.token, result.player);
}

export async function logout(): Promise<void> {
  try {
    await api<null>("/api/auth/logout", { method: "POST" });
  } finally {
    useSession.getState().clear();
  }
}

/**
 * 앱을 열 때 세션을 확인한다.
 * 게스트: 토큰이 아직 유효한지 묻고 새 토큰을 받는다(쓰는 동안 만료 30일 연장).
 * 회원: 토큰이 메모리에만 있으므로 리프레시 쿠키로 새로 받는다.
 */
export async function verifySession(): Promise<void> {
  const { token, player, clear } = useSession.getState();
  if (player?.kind === "MEMBER" && !token) {
    await refreshMemberSession();
    return;
  }
  if (!token) return;
  try {
    const { token: renewed, ...me } = await api<Player & { token: string }>("/api/players/me", { token });
    useSession.getState().setSession(renewed, me);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) clear();
    else throw error;
  }
}
