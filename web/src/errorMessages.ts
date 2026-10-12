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
  INVALID_CREDENTIALS: "아이디 또는 비밀번호가 맞지 않습니다.",
  USERNAME_TAKEN: "이미 쓰는 아이디입니다.",
  NICKNAME_TAKEN: "다른 회원이 쓰는 닉네임입니다.",
  RATE_LIMITED: "시도가 너무 많습니다. 1분 뒤에 다시 해 주세요.",
  PROVIDER_DISABLED: "지금은 쓸 수 없는 로그인 방법입니다.",
};

export function errorMessage(code: string): string {
  return MESSAGES[code] ?? "오류가 발생했습니다. 잠시 후 다시 시도해 주세요.";
}
