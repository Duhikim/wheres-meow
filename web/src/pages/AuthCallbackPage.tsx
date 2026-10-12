import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router";
import { refreshMemberSession, useSession } from "../session/sessionStore";
import { resetSocket } from "../socket/socket";

/** 소셜 로그인에서 돌아온 화면. 서버가 심어 준 리프레시 쿠키로 토큰을 받는다(토큰은 주소에 싣지 않는다). */
export function AuthCallbackPage() {
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    resetSocket();
    refreshMemberSession()
      .then((token) => {
        if (!token) return setFailed(true);
        navigate(useSession.getState().player?.needsNickname ? "/me/nickname" : "/", { replace: true });
      })
      .catch(() => setFailed(true));
  }, [navigate]);

  return (
    <main className="page center">
      {failed ? (
        <>
          <p className="error">로그인에 실패했습니다. 다시 시도해 주세요.</p>
          <Link className="btn primary" to="/login">
            로그인으로
          </Link>
        </>
      ) : (
        <p className="muted">로그인하는 중…</p>
      )}
    </main>
  );
}
