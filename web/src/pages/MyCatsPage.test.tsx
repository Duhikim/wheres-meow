import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../session/sessionStore";
import { chooseSkin, MyCatsPage } from "./MyCatsPage";

const player = { id: "p1", kind: "GUEST" as const, nickname: "냥냥이", skin1p: 16, skin2p: 17 };

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

describe("chooseSkin", () => {
  it("[성공] 고른 슬롯의 스킨만 바꾼다", () => {
    expect(chooseSkin({ skin1p: 16, skin2p: 17 }, "1p", 9)).toEqual({ skin1p: 9, skin2p: 17 });
    expect(chooseSkin({ skin1p: 16, skin2p: 17 }, "2p", 9)).toEqual({ skin1p: 16, skin2p: 9 });
  });

  it("[성공] 다른 슬롯에 있는 고양이를 고르면 두 슬롯을 맞바꿔 서로 다르게 유지한다", () => {
    expect(chooseSkin({ skin1p: 16, skin2p: 17 }, "1p", 17)).toEqual({ skin1p: 17, skin2p: 16 });
  });
});

describe("MyCatsPage", () => {
  it("[성공] 고양이를 고르고 저장하면 서버에 보내고 세션의 내 정보를 갱신한다", async () => {
    useSession.getState().setSession("token", player);
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ...player, skin1p: 9 }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <MemoryRouter>
        <MyCatsPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByLabelText("턱시도"));
    fireEvent.click(screen.getByRole("button", { name: "저장" }));

    await waitFor(() => expect(useSession.getState().player?.skin1p).toBe(9));
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/players/me/skins");
    expect(init.method).toBe("PUT");
    expect(JSON.parse(init.body as string)).toEqual({ skin1p: 9, skin2p: 17 });
  });

  it("[실패] 바꾼 것이 없으면 저장 버튼이 비활성이다", () => {
    useSession.getState().setSession("token", player);
    render(
      <MemoryRouter>
        <MyCatsPage />
      </MemoryRouter>,
    );

    expect((screen.getByRole("button", { name: "저장" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
