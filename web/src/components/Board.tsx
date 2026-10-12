import { CatArt, DirtArt, GrassArt, PawArt, PawSwipeArt } from "../art/Art";
import { SKIN_ACCENT, skinConfig } from "../art/skins";
import { BOARD_SIZE } from "../game/cellSize";
import { cellKey, type Cell, type LastMove, type SeatIndex } from "../game/types";

/** 끝난 뒤 공개되는, 아무도 못 찾은 고양이의 모양. 두 플레이어 스킨과 구분되도록 회색으로 흐리게 그린다. */
const UNFOUND_SKIN = 19;
const BOARD_PADDING_PX = 4; // .board 의 padding
const CELL_GAP_PX = 1; // .board 의 gap

interface BoardProps {
  skins: [number, number]; // 좌석별 스킨. 찾은 고양이를 찾은 사람의 스킨으로 그린다
  cells: Record<string, Cell>;
  cellSize: number;
  disabled: boolean; // 내 차례가 아니거나 대국이 끝났다
  pendingKey: string | null; // 서버 응답을 기다리는 칸
  onReveal: (x: number, y: number) => void;
  opponentMove?: LastMove | null; // 상대가 방금 연 칸. 있으면 앞발과 물결을 그 칸에 띄운다
}

function catSkin(seat: SeatIndex | null, skins: [number, number]): number {
  return seat === null ? UNFOUND_SKIN : skins[seat];
}

/** 상대 수 이펙트(시안 1-A+C): 상대 앞발이 내려와 칸을 톡 치고, 그 자리에서 상대 색 물결이 퍼진다. */
function OpponentMoveFx({ move, skin, cellSize }: { move: LastMove; skin: number; cellSize: number }) {
  const step = cellSize + CELL_GAP_PX;
  return (
    <div
      className="opp-move"
      aria-hidden
      style={{
        left: `${BOARD_PADDING_PX + move.x * step}px`,
        top: `${BOARD_PADDING_PX + move.y * step}px`,
        width: cellSize,
        height: cellSize,
        ["--opp" as string]: SKIN_ACCENT[skinConfig(skin).coat],
      }}
    >
      <PawSwipeArt skin={skin} className="opp-paw" />
      <span className="opp-ripple" />
      <span className="opp-ripple second" />
    </div>
  );
}

export function Board({ skins, cells, cellSize, disabled, pendingKey, onReveal, opponentMove }: BoardProps) {
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
        content = (
          <>
            <DirtArt index={index} className="ground" />
            {cell.n > 0 && <PawArt n={cell.n} className="mark" />}
          </>
        );
      } else if (cell?.kind === "cat") {
        skin = catSkin(cell.seat, skins);
        className = cell.seat === null ? "cell cat unfound" : `cell cat seat-${cell.seat}`;
        content = (
          <>
            <DirtArt index={index} className="ground" />
            <CatArt skin={skin} className="pop mark" />
          </>
        );
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
      {opponentMove && (
        <OpponentMoveFx key={opponentMove.version} move={opponentMove} skin={skins[opponentMove.seat]} cellSize={cellSize} />
      )}
    </div>
  );
}
