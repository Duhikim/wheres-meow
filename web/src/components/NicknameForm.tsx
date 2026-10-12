import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { ApiError } from "../api/http";
import { errorMessage } from "../errorMessages";
import { createGuest } from "../session/sessionStore";

export function NicknameForm() {
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createGuest(nickname);
    } catch (e) {
      setError(e instanceof ApiError ? errorMessage(e.code) : errorMessage("INTERNAL"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <label htmlFor="nickname">닉네임 (2~12자)</label>
      <input
        id="nickname"
        value={nickname}
        maxLength={12}
        autoComplete="off"
        onChange={(e) => setNickname(e.target.value)}
      />
      <button className="btn primary block" type="submit" disabled={submitting}>
        게스트로 시작
      </button>
      {error && <p className="error">{error}</p>}
      <p className="muted small">
        회원이신가요? <Link to="/login">로그인</Link> · <Link to="/signup">회원가입</Link>
      </p>
    </form>
  );
}
