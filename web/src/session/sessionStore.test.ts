import { afterEach, describe, expect, it, vi } from "vitest";
import { useSession, verifySession } from "./sessionStore";

const player = { id: "p1", kind: "GUEST" as const, nickname: "냥냥이", skin1p: 16, skin2p: 17 };

function mockFetch(status: number, body: unknown) {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status })));
}

afterEach(() => {
  vi.unstubAllGlobals();
  useSession.getState().clear();
});

describe("verifySession", () => {
  it("[성공] 서버가 토큰을 받아 주면 세션을 유지한다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(200, player);

    await verifySession();

    expect(useSession.getState().token).toBe("token");
  });

  it("[성공] 서버 재시작 등으로 토큰이 거부되면(401) 세션을 지운다", async () => {
    useSession.getState().setSession("stale", player);
    mockFetch(401, { code: "UNAUTHORIZED", message: "" });

    await verifySession();

    expect(useSession.getState().token).toBeNull();
    expect(useSession.getState().player).toBeNull();
  });

  it("[실패] 401 이 아닌 오류는 세션을 지우지 않고 그대로 던진다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(500, { code: "INTERNAL", message: "" });

    await expect(verifySession()).rejects.toThrow();
    expect(useSession.getState().token).toBe("token");
  });
});
