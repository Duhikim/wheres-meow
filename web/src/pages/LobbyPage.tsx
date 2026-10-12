import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/http";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useRoomStore, type WaitingRoom } from "../room/roomStore";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

export function LobbyPage() {
  const { token, player } = useSession();
  const lastError = useGameStore((s) => s.lastError);
  const { waitingRoom: room, setWaitingRoom, clearWaitingRoom } = useRoomStore();
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const rejoinedFor = useRef<string | null>(null);
  useNavigateOnGameStart();

  // 대기 중에 새로고침했다면 소켓을 다시 열고 같은 방에 재입장한다(서버는 방장 재입장을 멱등하게 처리)
  useEffect(() => {
    if (!token || !room || rejoinedFor.current === token) return;
    rejoinedFor.current = token;
    getSocket(token).emit("room:join", { code: room.code });
  }, [token, room]);

  if (!token || !player) {
    return (
      <main className="page">
        <h1 className="logo">Where's Meow</h1>
        <p className="muted">풀숲에 숨은 고양이를 먼저 찾아라</p>
        <NicknameForm />
      </main>
    );
  }

  const inviteLink = room ? `${window.location.origin}/r/${room.code}` : "";

  async function createRoom() {
    setError(null);
    try {
      const created = await api<WaitingRoom>("/api/rooms", { method: "POST", token });
      rejoinedFor.current = token;
      setWaitingRoom(created);
      getSocket(token!).emit("room:join", { code: created.code });
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    }
  }

  function cancelRoom() {
    if (room) getSocket(token!).emit("room:cancel", { code: room.code });
    clearWaitingRoom();
  }

  async function copyLink() {
    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);
  }

  if (room) {
    return (
      <main className="page center">
        <h2>친구를 기다리는 중</h2>
        <div className="room-code">{room.code}</div>
        <button className="primary" type="button" onClick={copyLink}>
          {copied ? "링크를 복사했습니다" : "초대 링크 복사"}
        </button>
        <p className="muted small">{inviteLink}</p>
        <button className="secondary" type="button" onClick={cancelRoom}>
          취소
        </button>
      </main>
    );
  }

  return (
    <main className="page">
      <h1 className="logo">Where's Meow</h1>
      <p className="muted">{player.nickname} (게스트)</p>
      <button className="primary" type="button" onClick={createRoom}>
        친구와 대결
      </button>
      {(error || lastError) && <p className="error">{error ?? errorMessage(lastError!)}</p>}
    </main>
  );
}
