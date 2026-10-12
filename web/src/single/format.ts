/** 클리어 시간 표시. 1분 미만은 "41.2초", 그 이상은 "1:23.4". 기록이 없으면 "—". */
export function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  const tenths = Math.floor(ms / 100);
  const minutes = Math.floor(tenths / 600);
  const seconds = (tenths % 600) / 10;
  if (minutes === 0) return `${seconds.toFixed(1)}초`;
  return `${minutes}:${seconds.toFixed(1).padStart(4, "0")}`;
}
