const pending = new Map<string, ReturnType<typeof setTimeout>>();

/**
 * 끝난 대국 화면을 떠났다고 다음 틱에 알린다. effect 정리 함수에서 바로 보내면
 * 개발 모드 StrictMode 의 정리·재실행만으로도 화면에 들어오자마자 재대결이 닫히므로,
 * 같은 대국 화면이 곧바로 다시 붙으면 cancelLeaveResult 로 취소한다.
 */
export function scheduleLeaveResult(gameId: string, send: () => void): void {
  cancelLeaveResult(gameId);
  pending.set(
    gameId,
    setTimeout(() => {
      pending.delete(gameId);
      send();
    }, 0),
  );
}

export function cancelLeaveResult(gameId: string): void {
  const timer = pending.get(gameId);
  if (timer === undefined) return;
  clearTimeout(timer);
  pending.delete(gameId);
}
