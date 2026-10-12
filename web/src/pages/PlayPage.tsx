import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { Board } from "../components/Board";
import { errorMessage } from "../errorMessages";
import { computeCellSize } from "../game/cellSize";
import { useGameStore } from "../game/gameStore";
import { useSecondsLeft, useViewportWidth } from "../game/hooks";
import { cellKey, type GameState } from "../game/types";
import { useSession } from "../session/sessionStore";
import { getSocket } from "../socket/socket";

const REASON_TEXT: Record<NonNullable<GameState["result"]>["reason"], string> = {
  ALL_FOUND: "고양이 25마리를 모두 찾았습니다",
  FORFEIT: "기권으로 끝났습니다",
  AUTO_FORFEIT: "시간 초과 3회 연속으로 자동 기권되었습니다",
};

export function PlayPage() {
  const { gameId } = useParams();
  const token = useSession((s) => s.token);
  const game = useGameStore((s) => s.game);
  const lastError = useGameStore((s) => s.lastError);
  const [pendingKey, setPendingKey] = useState<string | null>(null);
  const [confirmForfeit, setConfirmForfeit] = useState(false);
  const secondsLeft = useSecondsLeft(game?.turnDeadline ?? null);
  const cellSize = computeCellSize(useViewportWidth());

  // 새 이벤트가 오거나 오류가 오면 대기 중 표시를 푼다
  useEffect(() => setPendingKey(null), [game?.version, lastError]);

  if (!token || !game || game.gameId !== gameId) {
    return (
      <main className="page center">
        <p>대국 정보를 불러올 수 없습니다.</p>
        <Link to="/">로비로</Link>
      </main>
    );
  }

  const socket = getSocket(token);
  const me = game.mySeat;
  const opponent = (1 - me) as 0 | 1;
  const myTurn = game.status === "IN_PROGRESS" && game.currentSeat === me;

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
      <header className="scoreboard">
        <div className="seat seat-0-text">
          <b>{game.seats[me].nickname}</b>
          <small>나</small>
          <span className="score">{game.seats[me].score}</span>
        </div>
        <span className="vs">VS</span>
        <div className="seat seat-1-text right">
          <span className="score">{game.seats[opponent].score}</span>
          <b>{game.seats[opponent].nickname}</b>
          <small>상대</small>
        </div>
      </header>

      {game.status === "IN_PROGRESS" && (
        <div className="turn">
          <span>{myTurn ? "🐾 내 차례" : "상대 차례"}</span>
          <span>{secondsLeft ?? ""}초</span>
          <div className="timer-bar">
            <i style={{ width: `${((secondsLeft ?? 0) / 20) * 100}%` }} />
          </div>
        </div>
      )}

      <Board
        cells={game.cells}
        cellSize={cellSize}
        disabled={!myTurn}
        pendingKey={pendingKey}
        onReveal={reveal}
      />

      {lastError && <p className="error">{errorMessage(lastError)}</p>}
      {game.outOfSync && game.status === "IN_PROGRESS" && (
        <p className="error">
          연결이 끊긴 사이 화면이 서버와 어긋났습니다. 대국이 끝나면 결과가 표시됩니다.{" "}
          <Link to="/">로비로</Link>
        </p>
      )}

      <footer className="play-footer">
        <span>
          숨은 고양이 <b>{25 - Object.values(game.cells).filter((c) => c.kind === "cat" && c.seat !== null).length}</b>마리
        </span>
        {game.status === "IN_PROGRESS" &&
          (confirmForfeit ? (
            <span>
              <button className="danger" type="button" onClick={forfeit}>
                기권 확정
              </button>
              <button className="ghost" type="button" onClick={() => setConfirmForfeit(false)}>
                계속하기
              </button>
            </span>
          ) : (
            <button className="ghost" type="button" onClick={() => setConfirmForfeit(true)}>
              기권
            </button>
          ))}
      </footer>

      {game.result && (
        <section className="result">
          <h2>
            {game.result.winner === null ? "무승부" : game.result.winner === me ? "승리!" : "패배"}
          </h2>
          <p className="big">
            {game.seats[me].score} : {game.seats[opponent].score}
          </p>
          <p className="muted">{REASON_TEXT[game.result.reason]}</p>
          <Link className="primary" to="/">
            로비로
          </Link>
        </section>
      )}
    </main>
  );
}
