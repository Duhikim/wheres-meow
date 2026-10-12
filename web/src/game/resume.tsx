import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { api } from "../api/http";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

/**
 * 앱을 열었을 때(새로고침 포함) 진행 중인 대국이 있으면 그 화면으로 보내고 전체 상태를 요청한다.
 * 화면은 그리지 않는다. 라우터 안에 한 번만 둔다.
 */
export function ResumeCurrentGame() {
  const token = useSession((s) => s.token);
  const navigate = useNavigate();
  const checkedFor = useRef<string | null>(null);

  useEffect(() => {
    if (!token || checkedFor.current === token) return;
    checkedFor.current = token;
    api<{ gameId: string } | null>("/api/games/current", { token })
      .then((current) => {
        if (!current) return;
        getSocket(token).emit("game:sync", { gameId: current.gameId });
        navigate(`/play/${current.gameId}`);
      })
      .catch((error) => console.error("진행 중인 대국 확인 실패", error));
  }, [token, navigate]);

  return null;
}
