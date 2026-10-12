import { cellKey, type Cell, type CellPayload, type GameAction, type GameState } from "./types";

function withUnfoundCats(cells: Record<string, Cell>, cats: [number, number][]): Record<string, Cell> {
  const next = { ...cells };
  for (const [x, y] of cats) {
    const key = cellKey(x, y);
    if (!next[key]) next[key] = { kind: "cat", seat: null };
  }
  return next;
}

function toCell(payload: CellPayload): Cell {
  return payload.kind === "cat" ? { kind: "cat", seat: payload.seat } : { kind: "number", n: payload.n };
}

function withCells(cells: Record<string, Cell>, added: CellPayload[]): Record<string, Cell> {
  const next = { ...cells };
  for (const cell of added) next[cellKey(cell.x, cell.y)] = toCell(cell);
  return next;
}

function withScores(state: GameState, scores: [number, number]): GameState["seats"] {
  return [
    { ...state.seats[0], score: scores[0] },
    { ...state.seats[1], score: scores[1] },
  ];
}

/** 서버 이벤트를 version 순서대로만 적용한다. 순서가 어긋나면 적용하지 않고 outOfSync 로 표시한다. */
export function gameReducer(state: GameState | null, action: GameAction): GameState | null {
  if (action.type === "started") {
    const p = action.payload;
    return {
      gameId: p.gameId,
      mode: p.mode,
      mySeat: p.mySeat,
      seats: p.seats,
      currentSeat: p.currentSeat,
      turnDeadline: p.turnDeadline,
      version: p.version,
      cells: withCells({}, p.cells),
      status: "IN_PROGRESS",
      result: null,
      outOfSync: false,
    };
  }
  if (action.type === "state") {
    // 재동기화: 서버의 전체 상태로 통째로 바꾼다. 같은 대국이 아니어도(새로고침 직후) 그대로 받는다.
    const p = action.payload;
    const finished = p.status === "FINISHED";
    const cells = withCells({}, p.cells);
    return {
      gameId: p.gameId,
      mode: p.mode,
      mySeat: p.mySeat,
      seats: p.seats,
      currentSeat: p.currentSeat,
      turnDeadline: finished ? null : p.turnDeadline,
      version: p.version,
      cells: finished && p.cats ? withUnfoundCats(cells, p.cats) : cells,
      status: p.status,
      result: p.result,
      outOfSync: false,
    };
  }
  if (!state || action.payload.gameId !== state.gameId) return state;
  // 종료 이벤트는 점수·승자·고양이 전체를 담은 최종 상태라서, 앞 이벤트를 놓쳤어도 적용한다
  if (action.type !== "ended" && action.payload.version !== state.version + 1) {
    return { ...state, outOfSync: true };
  }

  switch (action.type) {
    case "revealed": {
      const p = action.payload;
      return {
        ...state,
        cells: withCells(state.cells, p.cells),
        seats: withScores(state, p.scores),
        currentSeat: p.currentSeat,
        turnDeadline: p.turnDeadline,
        version: p.version,
      };
    }
    case "timeout": {
      const p = action.payload;
      return {
        ...state,
        seats: withScores(state, p.scores),
        currentSeat: p.currentSeat,
        turnDeadline: p.turnDeadline,
        version: p.version,
      };
    }
    case "ended": {
      const p = action.payload;
      return {
        ...state,
        cells: withUnfoundCats(state.cells, p.cats),
        seats: withScores(state, p.scores),
        turnDeadline: null,
        version: p.version,
        status: "FINISHED",
        result: { reason: p.reason, winner: p.winner, ratingChanges: p.ratingChanges },
      };
    }
  }
}
