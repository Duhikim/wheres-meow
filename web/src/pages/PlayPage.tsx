import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import { CatArt } from "../art/Art";
import { SKIN_ACCENT, skinConfig } from "../art/skins";
import { Board } from "../components/Board";
import { errorMessage } from "../errorMessages";
import { computeCellSize } from "../game/cellSize";
import { useGameStore } from "../game/gameStore";
import { useSecondsLeft, useViewportWidth } from "../game/hooks";
import { formatDelta, myRatingChange } from "../game/rating";
import { cellKey, type GameState, type SeatIndex } from "../game/types";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

const TURN_SECONDS = 20;
const TOTAL_CATS = 25;

const REASON_TEXT: Record<NonNullable<GameState["result"]>["reason"], string> = {
  ALL_FOUND: "고양이 25마리를 모두 찾았습니다",
  FORFEIT: "기권으로 끝났습니다",
  AUTO_FORFEIT: "시간 초과 3회 연속으로 자동 기권되었습니다",
};

const accentOf = (skin: number) => SKIN_ACCENT[skinConfig(skin).coat];

function SeatCard({ game, seat, mine }: { game: GameState; seat: SeatIndex; mine: boolean }) {
  const { nickname, skin, score } = game.seats[seat];
  const active = game.status === "IN_PROGRESS" && game.currentSeat === seat;
  return (
    <div className={`seat-card${active ? " active" : ""}${mine ? "" : " right"}`} style={{ ["--accent" as string]: accentOf(skin) }}>
      <CatArt skin={skin} pose="face" size={36} />
      <div className="seat-name">
        <b>{nickname}</b>
        <small>{mine ? "나" : "상대"}</small>
      </div>
      <span className="score">{score}</span>
    </div>
  );
}

export function PlayPage() {
  const { gameId } = useParams();
  const token = useSession((s) => s.token);
  const game = useGameStore((s) => s.game);
  const lastError = useGameStore((s) => s.lastError);
  const connection = useGameStore((s) => s.connection);
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [confirmForfeit, setConfirmForfeit] = useState(false);
  const secondsLeft = useSecondsLeft(game?.turnDeadline ?? null);
  const cellSize = computeCellSize(useViewportWidth());

  const syncRequested = useRef<string | null>(null);

  // 새 이벤트가 오거나 오류가 오면 대기 중 표시를 푼다
  useEffect(() => setPendingKey(null), [game?.version, lastError]);

  // 새로고침으로 들어왔거나(대국 정보 없음) 이벤트를 놓쳐 어긋났으면 서버에 전체 상태를 요청한다
  const needsSync = !game || game.gameId !== gameId || game.outOfSync;
  useEffect(() => {
    if (!token || !gameId || !needsSync) return;
    const key = `${gameId}:${game?.version ?? "none"}`;
    if (syncRequested.current === key) return;
    syncRequested.current = key;
    getSocket(token).emit("game:sync", { gameId });
  }, [token, gameId, needsSync, game?.version]);

  if (!token || !game || game.gameId !== gameId) {
    const failed = lastError === "GAME_NOT_FOUND" || lastError === "NOT_A_PARTICIPANT" || !token;
    return (
      <main className="page center">
        <CatArt skin={19} size={96} />
        <p>{failed ? "대국 정보를 불러올 수 없습니다. 이미 끝났거나 서버가 다시 시작되었습니다." : "대국을 불러오는 중…"}</p>
        {failed && (
          <Link className="btn primary" to="/">
            로비로
          </Link>
        )}
      </main>
    );
  }

  const socket = getSocket(token);
  const me = game.mySeat;
  const opponent = (1 - me) as SeatIndex;
  const myTurn = game.status === "IN_PROGRESS" && game.currentSeat === me;
  const botThinking = game.status === "IN_PROGRESS" && game.seats[game.currentSeat].isBot === true;
  const turnAccent = accentOf(game.seats[game.currentSeat].skin);
  const found = Object.values(game.cells).filter((c) => c.kind === "cat" && c.seat !== null).length;
  const skins: [number, number] = [game.seats[0].skin, game.seats[1].skin];
  const ratingChange = myRatingChange(game);

  function reveal(x: number, y: number) {
    useGameStore.getState().setError(null);
    setPendingKey(cellKey(x, y));
    socket.emit("game:reveal", { gameId: game!.gameId, x, y });
  }

  function forfeit() {
    socket.emit("game:forfeit", { gameId: game!.gameId });
    setConfirmForfeit(false);
  }

  return (
    <main className="play">
      {connection === "reconnecting" && <div className="banner">연결이 끊겼습니다. 다시 연결하는 중…</div>}

      <header className="scoreboard">
        <SeatCard game={game} seat={me} mine />
        <span className="vs">VS</span>
        <SeatCard game={game} seat={opponent} mine={false} />
      </header>

      {game.status === "IN_PROGRESS" && (
        <div className="turn" style={{ ["--accent" as string]: turnAccent }}>
          {botThinking ? (
            // 봇은 시간 제한이 없으므로 남은 시간 대신 생각하는 중임을 보여 준다
            <div className="turn-row">
              <span className="turn-label thinking">🤔 {game.seats[opponent].nickname} 생각하는 중…</span>
            </div>
          ) : (
            <>
              <div className="turn-row">
                <span className="turn-label">{myTurn ? "🐾 내 차례" : `${game.seats[opponent].nickname}의 차례`}</span>
                <span className="turn-seconds">{secondsLeft ?? ""}초</span>
              </div>
              <div className="timer-bar">
                <i style={{ width: `${((secondsLeft ?? 0) / TURN_SECONDS) * 100}%` }} />
              </div>
            </>
          )}
        </div>
      )}

      {game.result && (
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
          <Link className="btn primary" to="/">
            로비로
          </Link>
        </section>
      )}

      <Board skins={skins} cells={game.cells} cellSize={cellSize} disabled={!myTurn} pendingKey={pendingKey} onReveal={reveal} />

      {lastError && <p className="error">{errorMessage(lastError)}</p>}
      {game.outOfSync && game.status === "IN_PROGRESS" && (
        <p className="error">
          연결이 끊긴 사이 화면이 서버와 어긋났습니다. 대국이 끝나면 결과가 표시됩니다.{" "}
          <Link to="/">로비로</Link>
        </p>
      )}

      {game.status === "IN_PROGRESS" && (
        <footer className="play-footer">
          <span>
            숨은 고양이 <b>{TOTAL_CATS - found}</b>마리
          </span>
          {confirmForfeit ? (
            <span className="row">
              <button className="btn danger small" type="button" onClick={forfeit}>
                기권 확정
              </button>
              <button className="btn ghost small" type="button" onClick={() => setConfirmForfeit(false)}>
                계속하기
              </button>
            </span>
          ) : (
            <button className="btn ghost small" type="button" onClick={() => setConfirmForfeit(true)}>
              기권
            </button>
          )}
        </footer>
      )}

    </main>
  );
}
