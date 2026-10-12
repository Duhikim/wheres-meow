import { create } from "zustand";

export interface MatchWaiting {
  since: number; // 서버 기준 대기 시작 시각(epoch ms)
  range: number | null; // 처음 받아들이는 레이팅 차이. null 이면 제한 없음
}

interface MatchStore {
  waiting: MatchWaiting | null;
  waitingStartedAt: number | null; // 이 브라우저가 대기 상태를 받은 시각. 서버와 시계가 달라도 경과 시간이 맞게 보이도록 쓴다
  setWaiting: (waiting: MatchWaiting) => void;
  clearWaiting: () => void;
}

/**
 * 랜덤 매칭 대기 상태. 서버는 연결이 끊긴 사람을 대기열에서 빼므로 새로고침 뒤까지 남기지 않는다(메모리에만 둔다).
 * 같은 연결이 잠깐 끊겼다 다시 붙으면 bindGameEvents 가 다시 줄을 세운다.
 */
export const useMatchStore = create<MatchStore>((set, get) => ({
  waiting: null,
  waitingStartedAt: null,
  // 재연결로 다시 줄을 서도 화면의 경과 시간은 처음 누른 때부터 이어 간다
  setWaiting: (waiting) => set({ waiting, waitingStartedAt: get().waitingStartedAt ?? Date.now() }),
  clearWaiting: () => set({ waiting: null, waitingStartedAt: null }),
}));

/** 경과 시간에 따라 지금 받아들이는 레이팅 차이(서버 matchmaking/domain/queue.py 와 같은 규칙). null 이면 제한 없음. */
export function currentRange(initial: number | null, elapsedSeconds: number): number | null {
  if (initial === null || elapsedSeconds >= 30) return null;
  return initial + 50 * Math.floor(elapsedSeconds / 5);
}
