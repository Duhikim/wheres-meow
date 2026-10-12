import { useEffect, useRef } from "react";
import { Link, useParams } from "react-router";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

export function JoinRoomPage() {
  const { code = "" } = useParams();
  const token = useSession((s) => s.token);
  const lastError = useGameStore((s) => s.lastError);
  const joinedFor = useRef<string | null>(null);
  useNavigateOnGameStart();

  useEffect(() => {
    if (!token || joinedFor.current === token) return;
    joinedFor.current = token;
    useGameStore.getState().setError(null);
    getSocket(token).emit("room:join", { code });
  }, [token, code]);

  return (
    <main className="page center">
      <h2>초대받은 방 {code.toUpperCase()}</h2>
      {!token ? (
        <NicknameForm />
      ) : lastError ? (
        <>
          <p className="error">{errorMessage(lastError)}</p>
          <Link to="/">로비로</Link>
        </>
      ) : (
        <p className="muted">입장하는 중…</p>
      )}
    </main>
  );
}
