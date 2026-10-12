import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import { api, ApiError } from "../api/http";
import { SingleBoard } from "../components/SingleBoard";
import { SoundToggle } from "../components/SoundToggle";
import { playSound } from "../sound/sound";
import { errorMessage } from "../errorMessages";
import { computeCellSize } from "../game/cellSize";
import { useViewportWidth } from "../game/hooks";
import { useSession } from "../session/sessionStore";
import {
  chord,
  DIFFICULTIES,
  elapsedMs,
  LEVELS,
  newGame,
  remainingCats,
  reveal,
  seededRandom,
  toggleFlag,
  type Difficulty,
  type Random,
  type SingleState,
} from "../single/engine";
import type { SoundKind } from "../sound/sound";
import { formatDuration } from "../single/format";
import { SingleSelectPage } from "./SingleSelectPage";

interface ClearResponse {
  bestMs: number;
  newBest: boolean;
  clears: number;
}

/** 경과 시간을 0.1초마다 다시 그린다(진행 중일 때만). */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setNow(Date.now()), 100);
    return () => clearInterval(id);
  }, [active]);
  return active ? now : Date.now();
}

/** 한 번 눌러 바뀐 판으로 낼 소리. 고양이를 건드리면 울음, 숫자가 드러나면 발자국, 빈 흙만 열리면 흙 소리다. */
export function soundOfStep(before: SingleState, after: SingleState): SoundKind {
  if (after.status === "LOST") return "cat";
  for (const [key, n] of after.opened) if (!before.opened.has(key) && n > 0) return "paw";
  return "dirt";
}

function isDifficulty(raw: string | undefined): raw is Difficulty {
  return DIFFICULTIES.includes(raw as Difficulty);
}

export function SinglePlayPage() {
  const { difficulty } = useParams();
  if (!isDifficulty(difficulty)) return <SingleSelectPage />;
  return <SingleGame key={difficulty} difficulty={difficulty} />;
}

function SingleGame({ difficulty }: { difficulty: Difficulty }) {
  const { token, player } = useSession();
  const [searchParams] = useSearchParams();
  const seed = searchParams.get("seed"); // E2E·테스트가 판을 고정할 때만 쓴다
  const [state, setState] = useState(() => newGame(difficulty));
  const [flagMode, setFlagMode] = useState(false);
  const [clear, setClear] = useState<ClearResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const submitted = useRef(false);
  // 새 판마다 새로 만든다. 시드가 있으면 같은 시드로 같은 판이 나온다
  const makeRandom = (): Random => (seed ? seededRandom(Number(seed)) : Math.random);
  const random = useRef<Random>(makeRandom());
  const now = useNow(state.status === "PLAYING");
  const cellSize = computeCellSize(useViewportWidth(), state.width);
  const level = LEVELS[difficulty];

  // 이기면 클리어 시간을 한 번만 서버에 보낸다
  useEffect(() => {
    if (state.status !== "WON" || submitted.current || !token) return;
    submitted.current = true;
    api<ClearResponse>("/api/players/me/single-records", {
      method: "POST",
      body: { difficulty, elapsedMs: elapsedMs(state, state.endedAt!) },
      token,
    })
      .then(setClear)
      .catch((e) => setError(errorMessage(e instanceof ApiError ? e.code : "INTERNAL")));
  }, [state, difficulty, token]);

  // 갱신 함수(setState(s => ...))를 쓰지 않는다. 개발 모드 StrictMode 가 갱신 함수를 두 번 불러
  // 시드 난수를 두 번 소비하면 첫 칸의 고양이 배치가 달라진다. 누를 때마다 현재 상태로 한 번만 계산한다.
  function tap(x: number, y: number) {
    const key = `${x},${y}`;
    if (flagMode) {
      setState(toggleFlag(state, x, y));
      return;
    }
    const next = state.opened.has(key) ? chord(state, x, y, Date.now()) : reveal(state, x, y, Date.now(), random.current);
    if (next !== state) playSound(soundOfStep(state, next));
    setState(next);
  }

  function restart() {
    submitted.current = false;
    setClear(null);
    setError(null);
    setFlagMode(false);
    random.current = makeRandom();
    setState(newGame(difficulty));
  }

  const ended = state.status === "WON" || state.status === "LOST";

  return (
    <main className="page play single">
      <div className="single-bar">
        <Link to="/single">← {level.label}</Link>
        <span className="spacer" />
        <b>{`🐱 ${remainingCats(state)}`}</b>
        <b className="single-time">{formatDuration(elapsedMs(state, now))}</b>
        <SoundToggle />
      </div>

      {ended && (
        <section className="result-card" aria-label="연습 결과">
          <h2 className={state.status === "WON" ? "win" : ""}>{state.status === "WON" ? "성공!" : "고양이를 건드렸습니다"}</h2>
          {state.status === "WON" && <p className="result-time">{formatDuration(elapsedMs(state, state.endedAt!))}</p>}
          {clear?.newBest && <p className="rating-change up">최고 기록을 새로 세웠습니다!</p>}
          {clear && !clear.newBest && <p className="muted">{`최고 기록 ${formatDuration(clear.bestMs)}`}</p>}
          {error && <p className="error">{error}</p>}
          <div className="row-links">
            <button className="btn primary" type="button" onClick={restart}>
              다시 하기
            </button>
            <Link className="btn ghost" to="/single">
              난이도 선택
            </Link>
          </div>
        </section>
      )}

      <SingleBoard
        state={state}
        skin={player?.skin1p ?? 16}
        cellSize={cellSize}
        onTap={tap}
        onLongPress={(x, y) => setState(toggleFlag(state, x, y))}
      />

      <div className="single-actions">
        <button
          type="button"
          className={`btn ${flagMode ? "primary" : "secondary"}`}
          aria-pressed={flagMode}
          onClick={() => setFlagMode((on) => !on)}
          disabled={ended}
        >
          🚩 깃발 모드 {flagMode ? "켜짐" : "꺼짐"}
        </button>
        <button className="btn ghost" type="button" onClick={restart}>
          새 판
        </button>
      </div>
      <p className="muted small">길게 누르거나 오른쪽 클릭해도 깃발을 꽂습니다. 숫자를 누르면 깃발이 숫자만큼 있을 때 주변을 한꺼번에 엽니다.</p>
    </main>
  );
}
