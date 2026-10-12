const MESSAGES: Record<string, string> = {
  ROOM_NOT_FOUND: "방을 찾을 수 없습니다.",
  ROOM_FULL: "이미 대국이 시작된 방입니다.",
  ROOM_EXPIRED: "만료되었거나 취소된 방입니다.",
  NOT_YOUR_TURN: "상대 차례입니다.",
  CELL_ALREADY_OPEN: "이미 열린 칸입니다.",
  ALREADY_IN_GAME: "이미 진행 중인 대국이 있습니다.",
  GAME_FINISHED: "이미 끝난 대국입니다.",
  UNAUTHORIZED: "입장 정보가 만료되었습니다. 닉네임을 다시 입력해 주세요.",
  INVALID_INPUT: "입력값을 확인해 주세요.",
};

export function errorMessage(code: string): string {
  return MESSAGES[code] ?? "오류가 발생했습니다. 잠시 후 다시 시도해 주세요.";
}
