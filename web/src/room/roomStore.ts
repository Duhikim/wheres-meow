import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export interface WaitingRoom {
  code: string;
  status: string;
  expiresAt: number;
}

/** 이 오류를 받으면 기다리던 방은 더 이상 쓸 수 없다. */
export const ROOM_GONE_CODES = new Set(["ROOM_EXPIRED", "ROOM_NOT_FOUND", "ROOM_FULL"]);

interface RoomStore {
  waitingRoom: WaitingRoom | null;
  setWaitingRoom: (room: WaitingRoom) => void;
  clearWaitingRoom: () => void;
}

/**
 * 방장이 기다리는 방. 새로고침해도 같은 탭에서는 남도록 sessionStorage 에 둔다.
 * 남아 있으면 로비가 다시 열릴 때 같은 방에 재입장해서, 상대가 와도 대국 시작을 받을 수 있다.
 */
export const useRoomStore = create<RoomStore>()(
  persist(
    (set) => ({
      waitingRoom: null,
      setWaitingRoom: (room) => set({ waitingRoom: room }),
      clearWaitingRoom: () => set({ waitingRoom: null }),
    }),
    { name: "wheresmeow-waiting-room", storage: createJSONStorage(() => sessionStorage) },
  ),
);
