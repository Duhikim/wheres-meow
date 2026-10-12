import { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router";
import { api, ApiError } from "../api/http";
import { CatArt } from "../art/Art";
import { NicknameForm } from "../components/NicknameForm";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useElapsedSeconds, useNavigateOnGameStart, useSecondsLeft } from "../game/hooks";
import { currentRange, useMatchStore } from "../match/matchStore";
import { useRoomStore, type WaitingRoom } from "../room/roomStore";
import { logout, useSession } from "../session/sessionStore";
import { getSocket, resetSocket } from "../socket/socket";

function formatRemaining(seconds: number | null): string {
  if (seconds === null) return "";
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export function LobbyPage() {
  const { token, player } = useSession();
  const lastError = useGameStore((s) => s.lastError);
  const { waitingRoom: room, setWaitingRoom, clearWaitingRoom } = useRoomStore();
  const { waiting: matchWaiting, waitingStartedAt, clearWaiting: clearMatchWaiting } = useMatchStore();
  const matchElapsed = useElapsedSeconds(waitingStartedAt);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const rejoinedFor = useRef<string | null>(null);
  const remaining = useSecondsLeft(room?.expiresAt ?? null);
  useNavigateOnGameStart();

  // 이전 화면(대국·초대)에서 받은 오류 문구를 로비에 끌고 오지 않는다
  useEffect(() => useGameStore.getState().setError(null), []);

  // 대기 중에 새로고침했다면 소켓을 다시 열고 같은 방에 재입장한다(서버는 방장 재입장을 멱등하게 처리)
  useEffect(() => {
    if (!token || !room || rejoinedFor.current === token) return;
    rejoinedFor.current = token;
    getSocket(token).emit("room:join", { code: room.code });
  }, [token, room]);

  // 소셜 로그인으로 막 가입했으면 닉네임부터 정한다
  if (player?.needsNickname) return <Navigate to="/me/nickname" replace />;

  if (!token || !player) {
    return (
      <main className="page">
        <div className="logo">
          <CatArt skin={16} size={112} />
          <h1>Where's Meow</h1>
          <p>풀숲에 숨은 고양이를 먼저 찾아라</p>
        </div>
        <NicknameForm />
      </main>
    );
  }

  const inviteLink = room ? `${window.location.origin}/r/${room.code}` : "";
  const canShare = typeof navigator.share === "function";

  async function createRoom() {
    setError(null);
    useGameStore.getState().setError(null);
    try {
      const created = await api<WaitingRoom>("/api/rooms", { method: "POST", token });
      rejoinedFor.current = token;
      setWaitingRoom(created);
      setCopied(false);
      getSocket(token!).emit("room:join", { code: created.code });
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    }
  }

  function joinMatch() {
    setError(null);
    useGameStore.getState().setError(null);
    getSocket(token!).emit("match:join"); // 서버가 match:waiting 을 보내면 대기 화면으로 바뀐다
  }

  function leaveMatch() {
    getSocket(token!).emit("match:leave");
    clearMatchWaiting();
  }

  function cancelRoom() {
    if (room) getSocket(token!).emit("room:cancel", { code: room.code });
    clearWaitingRoom();
  }

  async function signOut() {
    resetSocket();
    await logout();
  }

  async function copyLink() {
    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);
  }

  async function shareLink() {
    try {
      await navigator.share({ title: "Where's Meow", text: "고양이 찾기 한 판 하자!", url: inviteLink });
    } catch {
      // 사용자가 공유 시트를 닫은 경우다. 따로 알릴 것이 없다.
    }
  }

  if (matchWaiting) {
    const range = currentRange(matchWaiting.range, matchElapsed);
    return (
      <main className="page center">
        <CatArt skin={player.skin1p} size={104} />
        <h2>상대를 찾는 중</h2>
        <div className="room-code" aria-label="기다린 시간">
          {formatRemaining(matchElapsed)}
        </div>
        <p className="muted">{range === null ? "레이팅과 관계없이 찾고 있습니다" : `레이팅 ±${range} 안에서 찾고 있습니다`}</p>
        {lastError && <p className="error">{errorMessage(lastError)}</p>}
        <button className="btn ghost" type="button" onClick={leaveMatch}>
          취소
        </button>
      </main>
    );
  }

  if (room) {
    const expired = remaining === 0;
    return (
      <main className="page center">
        <CatArt skin={player.skin1p} size={104} />
        <h2>친구를 기다리는 중</h2>
        <div className="room-code">{room.code}</div>
        <div className="stack">
          {canShare && (
            <button className="btn primary block" type="button" onClick={shareLink} disabled={expired}>
              초대 링크 보내기
            </button>
          )}
          <button className={`btn ${canShare ? "secondary" : "primary"} block`} type="button" onClick={copyLink} disabled={expired}>
            {copied ? "링크를 복사했습니다" : "초대 링크 복사"}
          </button>
        </div>
        <p className="muted small">{inviteLink}</p>
        <p className="muted">{expired ? "방이 만료되었습니다. 새로 만들어 주세요." : `${formatRemaining(remaining)} 뒤 방이 사라집니다`}</p>
        {lastError && <p className="error">{errorMessage(lastError)}</p>}
        <button className="btn ghost" type="button" onClick={cancelRoom}>
          {expired ? "돌아가기" : "취소"}
        </button>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="logo">
        <CatArt skin={player.skin1p} size={112} />
        <h1>Where's Meow</h1>
        <p>풀숲에 숨은 고양이를 먼저 찾아라</p>
      </div>
      <div className="who">
        <CatArt skin={player.skin1p} pose="face" size={36} />
        <div>
          <b>{player.nickname}</b>
          <small>{player.kind === "MEMBER" ? "회원" : "게스트"}</small>
        </div>
        <span className="spacer" />
        <Link className="small" to="/me/nickname">
          닉네임
        </Link>
        {player.kind === "MEMBER" ? (
          <button className="link-button small" type="button" onClick={signOut}>
            로그아웃
          </button>
        ) : (
          <Link className="small" to="/login">
            로그인
          </Link>
        )}
      </div>
      <button className="btn primary block" type="button" onClick={joinMatch}>
        ⚡ 빠른 대전
      </button>
      <button className="btn secondary block" type="button" onClick={createRoom}>
        친구와 대결
      </button>
      <Link className="btn secondary block" to="/bot">
        🤖 컴퓨터와 대결
      </Link>
      <Link className="btn secondary block" to="/single">
        🧩 혼자 연습
      </Link>
      <Link className="btn secondary block" to="/me/cats">
        🐱 내 고양이
      </Link>
      <div className="row-links">
        <Link className="btn ghost" to="/ranking">
          🏆 랭킹
        </Link>
        <Link className="btn ghost" to={`/players/${player.id}`}>
          📊 내 전적
        </Link>
      </div>
      {(error || lastError) && <p className="error">{error ?? errorMessage(lastError!)}</p>}
    </main>
  );
}
