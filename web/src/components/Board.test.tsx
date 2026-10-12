import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Board } from "./Board";

afterEach(cleanup);

describe("Board", () => {
  it("[성공] 12x12 칸을 그린다", () => {
    render(<Board skins={[16, 17]} cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={() => {}} />);

    expect(screen.getAllByRole("button")).toHaveLength(144);
  });

  it("[성공] 닫힌 칸을 누르면 좌표를 넘긴다", () => {
    const onReveal = vi.fn();
    render(<Board skins={[16, 17]} cells={{}} cellSize={28} disabled={false} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("3,5"));

    expect(onReveal).toHaveBeenCalledWith(3, 5);
  });

  it("[성공] 숫자 칸은 숫자를, 빈 칸은 아무것도 보여 주지 않는다", () => {
    render(
      <Board
        skins={[16, 17]}
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
    render(<Board skins={[16, 17]} cells={{}} cellSize={28} disabled={true} pendingKey={null} onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("0,0"));

    expect(onReveal).not.toHaveBeenCalled();
  });

  it("[실패] 서버 응답을 기다리는 동안에는 다른 칸을 누를 수 없다", () => {
    const onReveal = vi.fn();
    render(<Board skins={[16, 17]} cells={{}} cellSize={28} disabled={false} pendingKey="0,0" onReveal={onReveal} />);

    fireEvent.click(screen.getByLabelText("1,1"));

    expect(onReveal).not.toHaveBeenCalled();
  });
  it("[성공] 닫힌 칸은 들풀, 숫자 칸은 발자국 그림으로 그린다", () => {
    render(
      <Board skins={[16, 17]} cells={{ "0,0": { kind: "number", n: 3 } }} cellSize={28} disabled={false} pendingKey={null} onReveal={() => {}} />,
    );

    expect(screen.getByLabelText("1,0").querySelector("svg rect")).not.toBeNull();
    expect(screen.getByLabelText("0,0").querySelector("svg text")?.textContent).toBe("3");
  });

  it("[성공] 찾은 고양이는 찾은 사람의 스킨으로, 못 찾은 고양이는 따로 표시한다", () => {
    render(
      <Board
        skins={[9, 21]}
        cells={{ "0,0": { kind: "cat", seat: 1 }, "1,0": { kind: "cat", seat: 0 }, "2,0": { kind: "cat", seat: null } }}
        cellSize={28}
        disabled={false}
        pendingKey={null}
        onReveal={() => {}}
      />,
    );

    expect(screen.getByLabelText("0,0").dataset.skin).toBe("21");
    expect(screen.getByLabelText("1,0").dataset.skin).toBe("9");
    expect(screen.getByLabelText("2,0").className).toContain("unfound");
  });
});
