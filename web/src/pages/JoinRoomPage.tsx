import { useEffect, useRef } from "react";
import { Link, Navigate, useParams } from "react-router";
import { CatArt } from "../art/Art";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useRoomStore } from "../room/roomStore";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

export function JoinRoomPage() {
  const { code = "" } = useParams();
  const token = useSession((s) => s.token);
  const player = useSession((s) => s.player);
  const lastError = useGameStore((s) => s.lastError);
  const waitingRoom = useRoomStore((s) => s.waitingRoom);
  const joinedFor = useRef<string | null>(null);
  useNavigateOnGameStart();

  useEffect(() => {
    if (!token || joinedFor.current === token) return;
    joinedFor.current = token;
    useGameStore.getState().setError(null);
    getSocket(token).emit("room:join", { code });
  }, [token, code]);

  // 방장이 자기 초대 링크를 연 경우: 서버가 room:waiting 을 보내 대기 방이 저장된다 → 로비의 대기 화면으로
  if (waitingRoom && waitingRoom.code === code.toUpperCase()) return <Navigate to="/" replace />;

  return (
    <main className="page center">
      <CatArt skin={player?.skin1p ?? 16} size={96} />
      <h2>초대받은 방 {code.toUpperCase()}</h2>
      {!token ? (
        <>
          <p className="muted">닉네임을 정하면 바로 대국이 시작됩니다.</p>
          <NicknameForm />
        </>
      ) : lastError ? (
        <>
          <p className="error">{errorMessage(lastError)}</p>
          <Link className="btn primary" to="/">
            로비로
          </Link>
        </>
      ) : (
        <p className="muted">입장하는 중…</p>
      )}
    </main>
  );
}
