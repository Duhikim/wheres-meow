import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/http";
import { login, logout, refreshMemberSession, useSession, verifySession } from "./sessionStore";

const member = { id: "m1", kind: "MEMBER" as const, nickname: "고양이집사", skin1p: 16, skin2p: 17, needsNickname: false };

function respond(status: number, body: unknown) {
  return new Response(body === null ? null : JSON.stringify(body), { status });
}

afterEach(() => {
  vi.unstubAllGlobals();
  useSession.getState().clear();
  localStorage.clear();
});

describe("회원 세션", () => {
  it("[성공] 로그인하면 토큰과 내 정보를 갖는다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => respond(200, { token: "access-1", player: member })));

    await login("neko_01", "password1");

    expect(useSession.getState().token).toBe("access-1");
    expect(useSession.getState().player?.kind).toBe("MEMBER");
  });

  it("[성공] 회원의 액세스 토큰은 브라우저 저장소에 남기지 않는다", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => respond(200, { token: "access-1", player: member })));

    await login("neko_01", "password1");

    const saved = localStorage.getItem("wheresmeow-session") ?? "";
    expect(saved).not.toContain("access-1");
    expect(saved).toContain("고양이집사");
  });

  it("[성공] 앱을 열 때 회원 토큰이 없으면 리프레시 쿠키로 새 토큰을 받는다", async () => {
    useSession.setState({ token: null, player: member });
    const fetchMock = vi.fn(async (_url: string) => respond(200, { token: "access-2", player: member }));
    vi.stubGlobal("fetch", fetchMock);

    await verifySession();

    expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/refresh");
    expect(useSession.getState().token).toBe("access-2");
  });

  it("[성공] 여러 곳에서 동시에 리프레시를 불러도 요청은 하나만 보내고 결과를 나눠 갖는다", async () => {
    useSession.setState({ token: null, player: member });
    let resolveFetch: (r: Response) => void = () => {};
    const fetchMock = vi.fn(() => new Promise<Response>((resolve) => (resolveFetch = resolve)));
    vi.stubGlobal("fetch", fetchMock);

    const first = refreshMemberSession();
    const second = refreshMemberSession();
    resolveFetch(respond(200, { token: "only-one", player: member }));

    expect(await Promise.all([first, second])).toEqual(["only-one", "only-one"]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("[실패] 리프레시가 거부되면 세션을 지운다", async () => {
    useSession.setState({ token: null, player: member });
    vi.stubGlobal("fetch", vi.fn(async () => respond(401, { code: "UNAUTHORIZED", message: "" })));

    await verifySession();

    expect(useSession.getState().player).toBeNull();
  });

  it("[성공] 회원 요청이 401 이면 한 번 리프레시하고 새 토큰으로 다시 보낸다", async () => {
    useSession.setState({ token: "expired", player: member });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(respond(401, { code: "UNAUTHORIZED", message: "" }))
      .mockResolvedValueOnce(respond(200, { token: "fresh", player: member }))
      .mockResolvedValueOnce(respond(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await api<{ ok: boolean }>("/api/rooms", { method: "POST", token: "expired" });

    expect(result).toEqual({ ok: true });
    expect(fetchMock.mock.calls[1][0]).toBe("/api/auth/refresh");
    const retried = fetchMock.mock.calls[2][1] as RequestInit;
    expect((retried.headers as Record<string, string>).Authorization).toBe("Bearer fresh");
  });

  it("[성공] 로그아웃하면 서버에 알리고 세션을 지운다", async () => {
    useSession.setState({ token: "access-1", player: member });
    const fetchMock = vi.fn(async (_url: string) => respond(204, null));
    vi.stubGlobal("fetch", fetchMock);

    await logout();

    expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/logout");
    expect(useSession.getState().player).toBeNull();
  });
});
