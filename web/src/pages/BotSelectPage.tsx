import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router";
import { api } from "../api/http";
import { CatArt } from "../art/Art";
import { errorMessage } from "../errorMessages";
import { useGameStore } from "../game/gameStore";
import { useNavigateOnGameStart } from "../game/hooks";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

type Difficulty = "EASY" | "NORMAL" | "HARD";

interface BotRecord {
  difficulty: Difficulty;
  wins: number;
  losses: number;
  draws: number;
}

const LEVELS: { difficulty: Difficulty; label: string; description: string; skin: number }[] = [
  { difficulty: "EASY", label: "쉬움", description: "가끔 확실한 고양이를 찾지만 대부분 아무 데나 엽니다.", skin: 21 },
  { difficulty: "NORMAL", label: "보통", description: "숫자 하나로 보이는 고양이는 놓치지 않습니다.", skin: 19 },
  { difficulty: "HARD", label: "어려움", description: "여러 숫자를 엮어 확률이 가장 높은 칸을 고릅니다.", skin: 9 },
];

export function BotSelectPage() {
  const { token, player } = useSession();
  const lastError = useGameStore((s) => s.lastError);
  const [records, setRecords] = useState<BotRecord[] | null>(null);
  const [starting, setStarting] = useState<Difficulty | null>(null);
  useNavigateOnGameStart();

  useEffect(() => {
    if (!token) return;
    useGameStore.getState().setError(null);
    api<BotRecord[]>("/api/players/me/bot-records", { token })
      .then(setRecords)
      .catch((error) => console.error("봇 전적 조회 실패", error));
  }, [token]);

  if (!token || !player) return <Navigate to="/" replace />;

  function start(difficulty: Difficulty) {
    setStarting(difficulty);
    useGameStore.getState().setError(null);
    getSocket(token!).emit("bot:start", { difficulty });
  }

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      <h2>컴퓨터와 대결</h2>
      <p className="muted">난이도를 고르면 바로 시작합니다. 컴퓨터 대전은 레이팅에 반영되지 않습니다.</p>
      <div className="stack">
        {LEVELS.map(({ difficulty, label, description, skin }) => {
          const record = records?.find((r) => r.difficulty === difficulty);
          return (
            <button
              key={difficulty}
              type="button"
              className="level-card"
              disabled={starting !== null && !lastError}
              onClick={() => start(difficulty)}
            >
              <CatArt skin={skin} size={56} />
              <span className="level-text">
                <b>{label}</b>
                <small>{description}</small>
                {record && <small className="level-record">{`${record.wins}승 ${record.losses}패 ${record.draws}무`}</small>}
              </span>
            </button>
          );
        })}
      </div>
      {starting && !lastError && <p className="muted">대국을 준비하는 중…</p>}
      {lastError && <p className="error">{errorMessage(lastError)}</p>}
    </main>
  );
}
