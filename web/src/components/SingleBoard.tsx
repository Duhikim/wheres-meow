import { useRef } from "react";
import { CatArt, GrassArt, PawArt } from "../art/Art";
import type { SingleState } from "../single/engine";

const LONG_PRESS_MS = 400;
const UNFOUND_SKIN = 19; // 대전 판의 "아무도 못 찾은 고양이"와 같은 회색

interface Props {
  state: SingleState;
  skin: number; // 끝난 뒤 깃발로 맞힌 고양이를 그릴 내 고양이
  cellSize: number;
  onTap: (x: number, y: number) => void;
  onLongPress: (x: number, y: number) => void;
}

/** 혼자 연습 판. 짧게 누르면 onTap, 길게 누르면 onLongPress(깃발). 길게 누른 뒤 따라오는 클릭은 무시한다. */
export function SingleBoard({ state, skin, cellSize, onTap, onLongPress }: Props) {
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const longPressed = useRef(false);
  const ended = state.status === "WON" || state.status === "LOST";

  function startPress(x: number, y: number) {
    longPressed.current = false;
    timer.current = setTimeout(() => {
      longPressed.current = true;
      onLongPress(x, y);
    }, LONG_PRESS_MS);
  }

  function cancelPress() {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }

  function click(x: number, y: number) {
    cancelPress();
    if (longPressed.current) {
      longPressed.current = false;
      return;
    }
    onTap(x, y);
  }

  const buttons = [];
  for (let y = 0; y < state.height; y++) {
    for (let x = 0; x < state.width; x++) {
      const key = `${x},${y}`;
      const n = state.opened.get(key);
      const isCat = ended && state.cats?.has(key);
      const flagged = state.flags.has(key);
      let className = "cell closed";
      let content = (
        <>
          <GrassArt index={y * state.width + x} />
          {flagged && (
            <span className="flag" style={{ fontSize: Math.round(cellSize * 0.55) }}>
              🚩
            </span>
          )}
        </>
      );
      if (n !== undefined) {
        className = "cell open";
        content = n > 0 ? <PawArt n={n} /> : <></>;
      } else if (isCat) {
        const exploded = key === state.explodedKey;
        className = `cell cat${exploded ? " exploded" : flagged ? "" : " unfound"}`;
        content = <CatArt skin={flagged || state.status === "WON" ? skin : UNFOUND_SKIN} className={exploded ? "pop" : ""} />;
      } else if (ended && flagged) {
        className = "cell closed wrong-flag"; // 고양이가 없는데 깃발을 꽂았다
      }
      buttons.push(
        <button
          key={key}
          type="button"
          aria-label={key}
          className={className}
          style={{ width: cellSize, height: cellSize }}
          disabled={ended}
          onPointerDown={() => startPress(x, y)}
          onPointerUp={cancelPress}
          onPointerLeave={cancelPress}
          onContextMenu={(event) => {
            event.preventDefault(); // 데스크톱에서는 오른쪽 클릭도 깃발이다
            cancelPress();
            onLongPress(x, y);
          }}
          onClick={() => click(x, y)}
        >
          {content}
        </button>,
      );
    }
  }
  return (
    <div className="board" style={{ gridTemplateColumns: `repeat(${state.width}, ${cellSize}px)` }}>
      {buttons}
    </div>
  );
}
