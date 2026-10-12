export const BOARD_SIZE = 12;
const SIDE_GUTTER_PX = 24;
const MAX_CELL_PX = 40;

/** 화면 폭에 맞는 칸 크기(px). 대전 판(12열)은 폭 360px 폰에서 28px, 넓은 화면에서는 40px 로 제한한다. */
export function computeCellSize(viewportWidth: number, columns: number = BOARD_SIZE): number {
  return Math.floor(Math.min((viewportWidth - SIDE_GUTTER_PX) / columns, MAX_CELL_PX));
}
