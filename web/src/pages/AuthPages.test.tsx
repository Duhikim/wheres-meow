import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession } from "../session/sessionStore";
import { AuthCallbackPage } from "./AuthCallbackPage";
import { LoginPage } from "./LoginPage";

vi.mock("../socket/socket", () => ({ getSocket: () => ({ emit: vi.fn() }), resetSocket: vi.fn() }));

const member = { id: "m1", kind: "MEMBER" as const, nickname: "냥123456", skin1p: 16, skin2p: 17, needsNickname: true };

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<p>로비 화면</p>} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/me/nickname" element={<p>닉네임 설정 화면</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  it("[성공] 켜진 소셜 로그인 버튼만 보여 준다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ providers: ["kakao"] }), { status: 200 })));

    renderAt("/login");

    await waitFor(() => expect(screen.getByRole("link", { name: /카카오/ })).toBeTruthy());
    expect(screen.queryByRole("link", { name: /구글/ })).toBeNull();
    expect(screen.getByRole("link", { name: /카카오/ }).getAttribute("href")).toBe("/api/auth/oauth/kakao/authorize");
  });

  it("[성공] 아이디와 비밀번호로 로그인하면 로비로 간다", async () => {
    const fetchMock = vi.fn(async (url: string) =>
      url === "/api/auth/providers"
        ? new Response(JSON.stringify({ providers: [] }), { status: 200 })
        : new Response(JSON.stringify({ token: "access-1", player: { ...member, needsNickname: false } }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderAt("/login");

    fireEvent.change(screen.getByLabelText("아이디"), { target: { value: "neko_01" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password1" } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(screen.getByText("로비 화면")).toBeTruthy());
    expect(useSession.getState().token).toBe("access-1");
  });
});

describe("AuthCallbackPage", () => {
  it("[성공] 소셜 로그인으로 처음 가입했으면 닉네임 설정 화면으로 보낸다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ token: "access-1", player: member }), { status: 200 })));

    renderAt("/auth/callback?new=1");

    await waitFor(() => expect(screen.getByText("닉네임 설정 화면")).toBeTruthy());
  });

  it("[실패] 리프레시가 실패하면 로그인 화면 대신 오류를 보여 준다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ code: "UNAUTHORIZED", message: "" }), { status: 401 })));

    renderAt("/auth/callback?new=0");

    await waitFor(() => expect(screen.getByText(/로그인에 실패했습니다/)).toBeTruthy());
  });
});
