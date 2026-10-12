import { CatArt, GrassArt, PawArt } from "../art/Art";
import { BOARD_SIZE } from "../game/cellSize";
import { cellKey, type Cell, type SeatIndex } from "../game/types";

/** 끝난 뒤 공개되는, 아무도 못 찾은 고양이의 모양. 두 플레이어 스킨과 구분되도록 회색으로 흐리게 그린다. */
const UNFOUND_SKIN = 19;

interface BoardProps {
  skins: [number, number]; // 좌석별 스킨. 찾은 고양이를 찾은 사람의 스킨으로 그린다
  cells: Record<string, Cell>;
  cellSize: number;
  disabled: boolean; // 내 차례가 아니거나 대국이 끝났다
  pendingKey: string | null; // 서버 응답을 기다리는 칸
  onReveal: (x: number, y: number) => void;
}

function catSkin(seat: SeatIndex | null, skins: [number, number]): number {
  return seat === null ? UNFOUND_SKIN : skins[seat];
}

export function Board({ skins, cells, cellSize, disabled, pendingKey, onReveal }: BoardProps) {
  const buttons = [];
  for (let y = 0; y < BOARD_SIZE; y++) {
    for (let x = 0; x < BOARD_SIZE; x++) {
      const key = cellKey(x, y);
      const cell = cells[key];
      const index = y * BOARD_SIZE + x;
      let className = "cell closed";
      let content = <GrassArt index={index} />;
      let skin: number | undefined;
      if (cell?.kind === "number") {
        className = "cell open";
        content = cell.n > 0 ? <PawArt n={cell.n} /> : <></>;
      } else if (cell?.kind === "cat") {
        skin = catSkin(cell.seat, skins);
        className = cell.seat === null ? "cell cat unfound" : `cell cat seat-${cell.seat}`;
        content = <CatArt skin={skin} className="pop" />;
      } else if (key === pendingKey) {
        className = "cell closed pending";
      }
      buttons.push(
        <button
          key={key}
          type="button"
          aria-label={`${x},${y}`}
          data-skin={skin}
          className={className}
          style={{ width: cellSize, height: cellSize }}
          disabled={disabled || cell !== undefined || pendingKey !== null}
          onClick={() => onReveal(x, y)}
        >
          {content}
        </button>,
      );
    }
  }
  return (
    <div className="board" style={{ gridTemplateColumns: `repeat(${BOARD_SIZE}, ${cellSize}px)` }}>
      {buttons}
    </div>
  );
}
