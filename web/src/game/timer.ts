import { useEffect, useState } from "react";

export const TURN_MS = 20_000;
const URGENT_MS = 5_000;

export interface TurnTimer {
  fraction: number; // 남은 시간 / 20초, 0~1
  seconds: number; // 화면에 쓰는 남은 초(올림)
  urgent: boolean; // 5초 이하
}

/** 마감 시각까지 남은 시간. 막대는 fraction 으로 매끄럽게 줄어들고, 숫자는 초 단위로 보여 준다. */
export function turnTimer(deadline: number, now: number): TurnTimer {
  const left = Math.max(0, deadline - now);
  return {
    fraction: Math.min(1, left / TURN_MS),
    seconds: Math.ceil(left / 1000),
    urgent: left <= URGENT_MS,
  };
}

/** 마감이 있는 동안 화면 주사율에 맞춰 다시 그린다. 마감이 없으면 null. */
export function useTurnTimer(deadline: number | null): TurnTimer | null {
  const [, setFrame] = useState(0);
  useEffect(() => {
    if (deadline === null) return;
    let id = requestAnimationFrame(function tick() {
      setFrame((frame) => frame + 1);
      id = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(id);
  }, [deadline]);
  return deadline === null ? null : turnTimer(deadline, Date.now());
}
