import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Board } from "./Board";

afterEach(cleanup);

describe("Board", () => {
  it("[성공] 12x12 칸을 그린다", () => {
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={() => {}} />);

    expect(screen.getAllByRole("button")).toHaveLength(144);
  });

  it("[성공] 닫힌 칸을 누르면 좌표를 넘긴다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("3,5"));

    expect(onReveal).toHaveBeenCalledWith(3, 5);
  });

  it("[성공] 숫자 칸은 숫자를, 빈 칸은 아무것도 보여 주지 않는다", () => {
    render(
      <Board
        cells={{ "0,0": { kind: "number", n: 2 }, "1,0": { kind: "number", n: 0 } }}
        cellSize={28}
        disabled={false}
        pendingKey={null}
        onReveal={() => {}}
      />,
    );

    expect(screen.getByLabelText("0,0").textContent).toBe("2");
    expect(screen.getByLabelText("1,0").textContent).toBe("");
  });

  it("[실패] 내 차례가 아니면 눌러도 아무 일도 없다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={true} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("0,0"));

    expect(onReveal).not.toHaveBeenCalled();
  });

  it("[실패] 서버 응답을 기다리는 동안에는 다른 칸을 누를 수 없다", () => {
    const onReveal = vi.fn();
    render(<Board cells={{}} cellSize={28} disabled={false} pendingKey="0,0" onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("1,1"));

    expect(onReveal).not.toHaveBeenCalled();
  });
});
