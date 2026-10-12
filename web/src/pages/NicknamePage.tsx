import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { ApiError } from "../api/http";
import { errorMessage } from "../errorMessages";
import { saveNickname, useSession } from "../session/sessionStore";

export function NicknamePage() {
  const navigate = useNavigate();
  const player = useSession((s) => s.player);
  const [nickname, setNickname] = useState(player?.needsNickname ? "" : (player?.nickname ?? ""));
  const [error, setError] = useState<string | null>(null);

  if (!player) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await saveNickname(nickname);
      navigate("/");
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    }
  }

  return (
    <main className="page">
      {!player.needsNickname && <Link to="/">← 로비</Link>}
      <h2>{player.needsNickname ? "닉네임을 정해 주세요" : "닉네임 바꾸기"}</h2>
      {player.kind === "MEMBER" && <p className="muted">회원 닉네임은 다른 회원과 겹칠 수 없습니다.</p>}
      <form className="stack" onSubmit={submit}>
        <label htmlFor="nn">닉네임 (2~12자)</label>
        <input id="nn" value={nickname} maxLength={12} onChange={(e) => setNickname(e.target.value)} />
        <button className="btn primary block" type="submit">
          저장
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  );
}
