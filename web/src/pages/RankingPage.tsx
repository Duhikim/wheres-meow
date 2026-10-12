import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api, ApiError } from "../api/http";
import { CatArt } from "../art/Art";
import { errorMessage } from "../errorMessages";

interface RankingEntry {
  rank: number;
  playerId: string;
  nickname: string;
  skin: number;
  rating: number;
  games: number;
  wins: number;
  losses: number;
  draws: number;
}

interface RankingPageBody {
  page: number;
  totalPages: number;
  entries: RankingEntry[];
}

export function RankingPage() {
  const [page, setPage] = useState(1);
  const [body, setBody] = useState<RankingPageBody | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api<RankingPageBody>(`/api/rankings?page=${page}`)
      .then(setBody)
      .catch((e) => setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL")));
  }, [page]);

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      <h2>랭킹</h2>
      <p className="muted small">레이팅 대국을 5판 이상 둔 회원만 나옵니다.</p>
      {error && <p className="error">{error}</p>}
      {body && body.entries.length === 0 && <p className="muted">아직 랭킹에 오른 회원이 없습니다. 첫 주인공이 되어 보세요!</p>}
      {body && body.entries.length > 0 && (
        <ol className="rank-list">
          {body.entries.map((e) => (
            <li key={e.playerId} className="rank-row">
              <span className="rank-no">{e.rank}</span>
              <CatArt skin={e.skin} pose="face" size={32} />
              <span className="rank-name">
                <Link to={`/players/${e.playerId}`}>{e.nickname}</Link>
                <small>{`${e.wins}승 ${e.losses}패 ${e.draws}무`}</small>
              </span>
              <b className="rank-rating">{e.rating}</b>
            </li>
          ))}
        </ol>
      )}
      {body && body.totalPages > 1 && (
        <div className="pager">
          <button className="btn ghost" type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            이전
          </button>
          <span className="muted">{`${page} / ${body.totalPages}`}</span>
          <button className="btn ghost" type="button" disabled={page >= body.totalPages} onClick={() => setPage(page + 1)}>
            다음
          </button>
        </div>
      )}
    </main>
  );
}
