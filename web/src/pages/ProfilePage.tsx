import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { api, ApiError } from "../api/http";
import { CatArt } from "../art/Art";
import { errorMessage } from "../errorMessages";
import { formatDelta } from "../game/rating";

interface RecentGame {
  gameId: string;
  mode: "INVITE" | "MATCH";
  endedAt: number;
  opponentId: string;
  opponentNickname: string;
  myScore: number;
  opponentScore: number;
  result: "WIN" | "LOSS" | "DRAW";
  ratingBefore: number | null;
  ratingAfter: number | null;
}

interface BotRecord {
  difficulty: "EASY" | "NORMAL" | "HARD";
  wins: number;
  losses: number;
  draws: number;
}

interface Profile {
  id: string;
  nickname: string;
  kind: "MEMBER" | "GUEST";
  skin: number;
  rating: number;
  games: number;
  wins: number;
  losses: number;
  draws: number;
  ranked: boolean;
  recentGames: RecentGame[];
  botRecords: BotRecord[];
}

const RESULT_TEXT = { WIN: "승", LOSS: "패", DRAW: "무" } as const;
const MODE_TEXT = { INVITE: "친구", MATCH: "매칭" } as const;
const LEVEL_TEXT = { EASY: "쉬움", NORMAL: "보통", HARD: "어려움" } as const;

function record(r: { wins: number; losses: number; draws: number }): string {
  return `${r.wins}승 ${r.losses}패 ${r.draws}무`;
}

function rankNote(profile: Profile): string {
  if (profile.kind === "GUEST") return "게스트는 랭킹에 오르지 않습니다. 회원으로 가입하면 이어서 기록됩니다.";
  if (!profile.ranked) return `랭킹에 오르려면 ${5 - profile.games}판 더 두어야 합니다.`;
  return "랭킹에 올라 있습니다.";
}

export function ProfilePage() {
  const { id } = useParams();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProfile(null);
    setError(null);
    api<Profile>(`/api/players/${encodeURIComponent(id ?? "")}`)
      .then(setProfile)
      .catch((e) => setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL")));
  }, [id]);

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      {error && <p className="error">{error}</p>}
      {profile && (
        <>
          <div className="profile-head">
            <CatArt skin={profile.skin} size={72} />
            <div>
              <h2>{profile.nickname}</h2>
              <small className="muted">{profile.kind === "MEMBER" ? "회원" : "게스트"}</small>
            </div>
            <span className="spacer" />
            <div className="profile-rating">
              <small className="muted">레이팅</small>
              <b>{profile.rating}</b>
            </div>
          </div>
          <p>{record(profile)}</p>
          <p className="muted small">{rankNote(profile)}</p>

          <h3>최근 대국</h3>
          {profile.recentGames.length === 0 && <p className="muted">아직 사람과 둔 대국이 없습니다.</p>}
          <ul className="recent-list">
            {profile.recentGames.map((g) => (
              <li key={g.gameId} className={`recent-row ${g.result.toLowerCase()}`}>
                <span className="recent-result">{RESULT_TEXT[g.result]}</span>
                <span className="recent-name">
                  <Link to={`/players/${g.opponentId}`}>{g.opponentNickname}</Link>
                  <small>{`${MODE_TEXT[g.mode]} · ${g.myScore}:${g.opponentScore}`}</small>
                </span>
                {g.ratingBefore !== null && g.ratingAfter !== null && (
                  <span className="recent-delta">{formatDelta(g.ratingAfter - g.ratingBefore)}</span>
                )}
              </li>
            ))}
          </ul>

          <h3>컴퓨터 대전</h3>
          <ul className="recent-list">
            {profile.botRecords.map((r) => (
              <li key={r.difficulty} className="recent-row">
                <span className="recent-name">{LEVEL_TEXT[r.difficulty]}</span>
                <span>{record(r)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  );
}
