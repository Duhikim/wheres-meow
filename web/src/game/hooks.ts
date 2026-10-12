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

/** 마감 시각까지 남은 초(올림). 마감이 없으면 null. */
export function useSecondsLeft(deadline: number | null): number | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (deadline === null) return;
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, [deadline]);
  return deadline === null ? null : Math.max(0, Math.ceil((deadline - now) / 1000));
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
