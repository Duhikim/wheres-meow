import { BOARD_SIZE } from "../game/cellSize";
import { cellKey, type Cell } from "../game/types";

interface BoardProps {
  cells: Record<string, Cell>;
  cellSize: number;
  disabled: boolean; // 내 차례가 아니거나 대국이 끝났다
  pendingKey: string | null; // 서버 응답을 기다리는 칸
  onReveal: (x: number, y: number) => void;
}

// 1단계의 임시 표현. 3단계에서 고양이 스킨·들풀·발자국 SVG 로 바꾼다.
function label(cell: Cell | undefined): string {
  if (!cell) return "";
  if (cell.kind === "cat") return "🐱";
  return cell.n > 0 ? String(cell.n) : "";
}

function className(cell: Cell | undefined, pending: boolean): string {
  if (!cell) return pending ? "cell closed pending" : "cell closed";
  if (cell.kind === "number") return "cell open";
  return cell.seat === null ? "cell cat unfound" : `cell cat seat-${cell.seat}`;
}

export function Board({ cells, cellSize, disabled, pendingKey, onReveal }: BoardProps) {
  const buttons = [];
  for (let y = 0; y < BOARD_SIZE; y++) {
    for (let x = 0; x < BOARD_SIZE; x++) {
      const key = cellKey(x, y);
      const cell = cells[key];
      buttons.push(
        <button
          key={key}
          type="button"
          aria-label={`${x},${y}`}
          className={className(cell, key === pendingKey)}
          style={{ width: cellSize, height: cellSize, fontSize: cellSize * 0.5 }}
          disabled={disabled || cell !== undefined || pendingKey !== null}
          onClick={() => onReveal(x, y)}
        >
          {label(cell)}
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
