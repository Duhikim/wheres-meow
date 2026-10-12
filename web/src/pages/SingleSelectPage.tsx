import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router";
import { api } from "../api/http";
import { CatArt } from "../art/Art";
import { DIFFICULTIES, LEVELS, type Difficulty } from "../single/engine";
import { formatDuration } from "../single/format";
import { useSession } from "../session/sessionStore";

export interface SingleRecord {
  difficulty: Difficulty;
  bestMs: number | null;
  clears: number;
}

const LEVEL_SKIN: Record<Difficulty, number> = { BEGINNER: 21, INTERMEDIATE: 16, EXPERT: 9 };

export function SingleSelectPage() {
  const { token, player } = useSession();
  const [records, setRecords] = useState<SingleRecord[] | null>(null);

  useEffect(() => {
    if (!token) return;
    api<SingleRecord[]>("/api/players/me/single-records", { token })
      .then(setRecords)
      .catch((error) => console.error("연습 기록 조회 실패", error));
  }, [token]);

  if (!token || !player) return <Navigate to="/" replace />;

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      <h2>혼자 연습</h2>
      <p className="muted">클래식 지뢰찾기입니다. 고양이를 건드리지 않고 나머지 칸을 모두 열면 성공입니다. 레이팅에는 반영되지 않고 최고 기록만 남습니다.</p>
      <div className="stack">
        {DIFFICULTIES.map((difficulty) => {
          const level = LEVELS[difficulty];
          const record = records?.find((r) => r.difficulty === difficulty);
          return (
            <Link key={difficulty} className="level-card" to={`/single/${difficulty}`}>
              <CatArt skin={LEVEL_SKIN[difficulty]} size={56} />
              <span className="level-text">
                <b>{level.label}</b>
                <small>{`${level.width}×${level.height} · 고양이 ${level.cats}마리`}</small>
                {record && (
                  <small className="level-record">
                    {record.bestMs === null ? "기록 없음" : `최고 ${formatDuration(record.bestMs)}`}
                  </small>
                )}
              </span>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
