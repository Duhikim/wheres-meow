import { Link } from "react-router";
import { CatArt } from "../art/Art";
import { SKIN_ACCENT, skinConfig } from "../art/skins";
import { formatDelta, myRatingChange } from "../game/rating";
import type { GameState, RematchCancelReason, RematchState, SeatIndex } from "../game/types";

const REASON_TEXT: Record<NonNullable<GameState["result"]>["reason"], string> = {
  ALL_FOUND: "고양이 25마리를 모두 찾았습니다",
  FORFEIT: "기권으로 끝났습니다",
  AUTO_FORFEIT: "시간 초과 3회 연속으로 자동 기권되었습니다",
};

const CANCEL_TEXT: Record<RematchCancelReason, string> = {
  DECLINED: "상대가 재대결을 거절했습니다.",
  EXPIRED: "30초가 지나 재대결 신청이 취소되었습니다.",
  LEFT: "상대가 결과 화면을 떠났습니다.",
  UNAVAILABLE: "지금은 재대결을 시작할 수 없습니다.",
  I_DECLINED: "재대결을 거절했습니다.",
};

const accentOf = (skin: number) => SKIN_ACCENT[skinConfig(skin).coat];

interface Props {
  game: GameState;
  rematch: RematchState | null;
  onRequestRematch: () => void;
  onDeclineRematch: () => void;
  onLeave: () => void;
}

export function ResultCard({ game, rematch: anyRematch, onRequestRematch, onDeclineRematch, onLeave }: Props) {
  if (!game.result) return null;
  const me = game.mySeat;
  const opponent = (1 - me) as SeatIndex;
  const ratingChange = myRatingChange(game);
  const rematch = anyRematch?.gameId === game.gameId ? anyRematch : null;

  let rematchArea;
  if (rematch?.cancelled) {
    rematchArea = <p className="muted">{CANCEL_TEXT[rematch.cancelled]}</p>;
  } else if (rematch?.mine) {
    rematchArea = <p className="muted">재대결 신청을 보냈습니다. 상대의 응답을 기다리는 중…</p>;
  } else if (rematch?.theirs) {
    rematchArea = (
      <>
        <p>상대가 재대결을 신청했습니다.</p>
        <div className="row-links">
          <button className="btn primary" type="button" onClick={onRequestRematch}>
            수락
          </button>
          <button className="btn ghost" type="button" onClick={onDeclineRematch}>
            거절
          </button>
        </div>
      </>
    );
  } else {
    rematchArea = (
      <button className="btn secondary" type="button" onClick={onRequestRematch}>
        재대결 신청
      </button>
    );
  }

  return (
    <section className="result-card" aria-label="대국 결과">
      <h2 className={game.result.winner === me ? "win" : ""}>
        {game.result.winner === null ? "무승부" : game.result.winner === me ? "승리!" : "패배"}
      </h2>
      <div className="result-score">
        <CatArt skin={game.seats[me].skin} pose="face" size={44} />
        <b style={{ color: accentOf(game.seats[me].skin) }}>{game.seats[me].score}</b>
        <span>:</span>
        <b style={{ color: accentOf(game.seats[opponent].skin) }}>{game.seats[opponent].score}</b>
        <CatArt skin={game.seats[opponent].skin} pose="face" size={44} />
      </div>
      <p className="muted">{REASON_TEXT[game.result.reason]}</p>
      {ratingChange && (
        <p className="rating-change">
          레이팅 {ratingChange.before} → <b>{ratingChange.after}</b>{" "}
          <span className={ratingChange.delta >= 0 ? "up" : "down"}>({formatDelta(ratingChange.delta)})</span>
        </p>
      )}
      <p className="muted small">흐린 회색 고양이는 아무도 찾지 못한 고양이입니다.</p>
      {rematchArea}
      <Link className="btn primary" to="/" onClick={onLeave}>
        로비로
      </Link>
    </section>
  );
}
