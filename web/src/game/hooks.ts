import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useGameStore } from "./gameStore";
import type { GameState } from "./types";

/** 들어가야 할 대국 ID. 끝났거나 서버와 어긋난 대국으로는 다시 끌고 가지 않는다. */
export function gameIdToEnter(game: GameState | null): string | null {
  return game && game.status === "IN_PROGRESS" && !game.outOfSync ? game.gameId : null;
}

/** 진행 중인 대국이 생기면 대국 화면으로 이동한다. */
export function useNavigateOnGameStart(): void {
  const navigate = useNavigate();
  const gameId = useGameStore((s) => gameIdToEnter(s.game));
  useEffect(() => {
    if (gameId) navigate(`/play/${gameId}`);
  }, [gameId, navigate]);
}

/**
 * 마감 시각까지 남은 초(올림). 마감이 없으면 null.
 * 현재 시각은 그릴 때마다 새로 읽는다. 숨겨진 탭에서는 브라우저가 간격 타이머를 늦추므로,
 * 현재 시각을 상태에 담아 두면 새 마감이 왔을 때 오래된 값으로 계산되어 20초를 넘게 보인다.
 * 간격 타이머는 다시 그리게 만드는 역할만 한다.
 */
export function useSecondsLeft(deadline: number | null): number | null {
  const [, setTick] = useState(0);
  useEffect(() => {
    if (deadline === null) return;
    const id = setInterval(() => setTick((tick) => tick + 1), 250);
    return () => clearInterval(id);
  }, [deadline]);
  return deadline === null ? null : Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
}

/** start 부터 지난 초(내림). start 가 없으면 0. 1초마다 다시 그린다. */
export function useElapsedSeconds(start: number | null): number {
  const [, setTick] = useState(0);
  useEffect(() => {
    if (start === null) return;
    const id = setInterval(() => setTick((tick) => tick + 1), 1000);
    return () => clearInterval(id);
  }, [start]);
  return start === null ? 0 : Math.max(0, Math.floor((Date.now() - start) / 1000));
}

export function useViewportWidth(): number {
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return width;
}
