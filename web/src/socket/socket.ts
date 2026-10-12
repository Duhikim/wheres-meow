import { io, type Socket } from "socket.io-client";
import { bindGameEvents, useGameStore } from "../game/gameStore";
import { refreshMemberSession, useSession } from "../session/sessionStore";

let socket: Socket | null = null;
let socketPlayerId: string | null = null;

/**
 * 플레이어마다 연결 하나를 유지한다. 연결(재연결 포함)할 때마다 저장소의 최신 토큰을 쓰므로,
 * 회원 토큰이 15분마다 바뀌어도 연결을 새로 만들지 않는다. 다른 플레이어로 바뀌면 새로 연다.
 */
export function getSocket(token: string): Socket {
  const playerId = useSession.getState().player?.id ?? token;
  if (socket && socketPlayerId === playerId) return socket;
  resetSocket();
  socket = io({ auth: (cb) => cb({ token: useSession.getState().token ?? token }) });
  socketPlayerId = playerId;
  bindGameEvents(socket);
  socket.on("connect_error", (error) => {
    if (error.message !== "UNAUTHORIZED") return;
    const current = socket;
    if (useSession.getState().player?.kind === "MEMBER") {
      // 액세스 토큰이 만료됐다. 리프레시 쿠키로 새 토큰을 받아 다시 붙는다.
      refreshMemberSession()
        .then((fresh) => (fresh ? current?.connect() : resetSocket()))
        .catch((e) => console.error("소켓 재인증 실패", e));
      return;
    }
    // 게스트 토큰이 거부됐다(서버 DB 초기화 등). 세션을 지우고 닉네임을 다시 받는다.
    useGameStore.getState().setError("UNAUTHORIZED");
    useSession.getState().clear();
    resetSocket();
  });
  return socket;
}

/** 로그아웃·플레이어 변경 시 연결을 끊는다. */
export function resetSocket(): void {
  socket?.disconnect();
  socket = null;
  socketPlayerId = null;
}
