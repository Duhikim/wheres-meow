export const BOARD_SIZE = 12;
const SIDE_GUTTER_PX = 24;
const MAX_CELL_PX = 40;

/** 화면 폭에 맞는 칸 크기(px). 폭 360px 폰에서 28px, 넓은 화면에서는 40px 로 제한한다. */
export function computeCellSize(viewportWidth: number): number {
  return Math.floor(Math.min((viewportWidth - SIDE_GUTTER_PX) / BOARD_SIZE, MAX_CELL_PX));
}
