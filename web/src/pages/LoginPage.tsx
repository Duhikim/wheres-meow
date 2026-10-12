import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { api, ApiError } from "../api/http";
import { CatArt } from "../art/Art";
import { errorMessage } from "../errorMessages";
import { login } from "../session/sessionStore";
import { resetSocket } from "../socket/socket";

const PROVIDER_LABELS: Record<string, string> = { google: "구글로 계속하기", naver: "네이버로 계속하기", kakao: "카카오로 계속하기" };

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [providers, setProviders] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api<{ providers: string[] }>("/api/auth/providers")
      .then((r) => setProviders(r.providers))
      .catch((e) => console.error("소셜 로그인 목록 조회 실패", e));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      resetSocket(); // 게스트로 붙어 있던 연결을 끊고 회원으로 다시 붙게 한다
      await login(username, password);
      navigate("/");
    } catch (e) {
      setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      <div className="logo">
        <CatArt skin={16} size={88} />
        <h1>로그인</h1>
        <p>회원은 랭킹에 오르고 전적이 계정에 남습니다.</p>
      </div>
      <form className="stack" onSubmit={submit}>
        <label htmlFor="username">아이디</label>
        <input id="username" value={username} autoComplete="username" onChange={(e) => setUsername(e.target.value)} />
        <label htmlFor="password">비밀번호</label>
        <input
          id="password"
          type="password"
          value={password}
          autoComplete="current-password"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="btn primary block" type="submit" disabled={submitting}>
          로그인
        </button>
        {error && <p className="error">{error}</p>}
      </form>
      {providers.length > 0 && (
        <div className="stack">
          {providers.map((provider) => (
            <a key={provider} className={`btn social ${provider} block`} href={`/api/auth/oauth/${provider}/authorize`}>
              {PROVIDER_LABELS[provider] ?? provider}
            </a>
          ))}
        </div>
      )}
      <p className="muted">
        아직 회원이 아니신가요? <Link to="/signup">회원가입</Link>
      </p>
    </main>
  );
}
