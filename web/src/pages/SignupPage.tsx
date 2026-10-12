import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { ApiError } from "../api/http";
import { errorMessage } from "../errorMessages";
import { signup } from "../session/sessionStore";
import { resetSocket } from "../socket/socket";

const MISMATCH = "비밀번호가 서로 다릅니다.";

export function SignupPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const mismatch = passwordConfirm !== "" && passwordConfirm !== password;
  // 불일치로 막힌 뒤 바르게 고쳤으면 그 오류는 더 보이지 않는다
  const shownError = error === MISMATCH && passwordConfirm === password ? null : error;

  async function submit(event: FormEvent) {
    event.preventDefault();
    // 확인은 입력 실수를 막는 화면의 일이다. 서버에는 비밀번호 하나만 보낸다.
    if (passwordConfirm !== password) {
      setError(MISMATCH);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      resetSocket();
      await signup(username, password, nickname);
      navigate("/");
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <Link to="/login">← 로그인</Link>
      <h2>회원가입</h2>
      <p className="muted">게스트로 둔 전적은 옮겨지지 않습니다.</p>
      <form className="stack" onSubmit={submit}>
        <label htmlFor="su-username">아이디 (4~20자 영문 소문자·숫자·밑줄)</label>
        <input id="su-username" value={username} autoComplete="username" onChange={(e) => setUsername(e.target.value)} />
        <label htmlFor="su-password">비밀번호 (8자 이상)</label>
        <input
          id="su-password"
          type="password"
          value={password}
          autoComplete="new-password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <label htmlFor="su-password-confirm">비밀번호 확인</label>
        <input
          id="su-password-confirm"
          type="password"
          value={passwordConfirm}
          autoComplete="new-password"
          aria-invalid={mismatch}
          onChange={(e) => setPasswordConfirm(e.target.value)}
        />
        {mismatch && error !== MISMATCH && <p className="error small">{MISMATCH}</p>}
        <label htmlFor="su-nickname">닉네임 (2~12자, 회원끼리 겹칠 수 없음)</label>
        <input id="su-nickname" value={nickname} maxLength={12} onChange={(e) => setNickname(e.target.value)} />
        <button className="btn primary block" type="submit" disabled={submitting}>
          가입하기
        </button>
        {shownError && <p className="error">{shownError}</p>}
      </form>
    </main>
  );
}
