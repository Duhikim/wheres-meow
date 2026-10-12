import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/http";
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
  it("[성공] 서버가 토큰을 받아 주면 새로 받은 토큰과 내 정보로 갱신한다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(200, { ...player, skin1p: 9, token: "renewed" });

    await verifySession();

    expect(useSession.getState().token).toBe("renewed");
    expect(useSession.getState().player?.skin1p).toBe(9);
  });

  it("[성공] 서버 재시작 등으로 토큰이 거부되면(401) 세션을 지운다", async () => {
    useSession.getState().setSession("stale", player);
    mockFetch(401, { code: "UNAUTHORIZED", message: "" });

    await verifySession();

    expect(useSession.getState().token).toBeNull();
    expect(useSession.getState().player).toBeNull();
  });

  it("[성공] 앱을 켜 둔 채 API 가 401 을 받으면 세션을 지운다", async () => {
    useSession.getState().setSession("stale", player);
    mockFetch(401, { code: "UNAUTHORIZED", message: "" });

    await expect(api("/api/rooms", { method: "POST", token: "stale" })).rejects.toThrow();

    expect(useSession.getState().token).toBeNull();
  });

  it("[실패] 401 이 아닌 API 오류는 세션을 지우지 않는다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(409, { code: "ALREADY_IN_GAME", message: "" });

    await expect(api("/api/rooms", { method: "POST", token: "token" })).rejects.toThrow();

    expect(useSession.getState().token).toBe("token");
  });

  it("[실패] 401 이 아닌 오류는 세션을 지우지 않고 그대로 던진다", async () => {
    useSession.getState().setSession("token", player);
    mockFetch(500, { code: "INTERNAL", message: "" });

    await expect(verifySession()).rejects.toThrow();
    expect(useSession.getState().token).toBe("token");
  });
});
