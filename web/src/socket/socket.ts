import { io, type Socket } from "socket.io-client";
import { bindGameEvents, useGameStore } from "../game/gameStore";
import { useSession } from "../session/sessionStore";

let socket: Socket | null = null;
let socketToken: string | null = null;

/** 토큰마다 연결 하나를 유지한다. 토큰이 바뀌면 이전 연결을 끊고 새로 연다. */
export function getSocket(token: string): Socket {
  if (socket && socketToken === token) return socket;
  socket?.disconnect();
  socket = io({ auth: { token } });
  socketToken = token;
  bindGameEvents(socket);
  socket.on("connect_error", (error) => {
    // 서버가 토큰을 거부하면(서버 재시작 등) 세션을 지우고 닉네임을 다시 받는다
    if (error.message === "UNAUTHORIZED") {
      useGameStore.getState().setError("UNAUTHORIZED");
      useSession.getState().clear();
      socket?.disconnect();
      socket = null;
      socketToken = null;
    }
  });
  return socket;
}
