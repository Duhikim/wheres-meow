import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { useGameStore } from "./gameStore";

/** 진행 중인 대국이 생기면 대국 화면으로 이동한다. 끝난 대국은 무시한다. */
export function useNavigateOnGameStart(): void {
  const navigate = useNavigate();
  const gameId = useGameStore((s) => (s.game?.status === "IN_PROGRESS" ? s.game.gameId : null));
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
