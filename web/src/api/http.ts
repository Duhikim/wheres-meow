export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

let onUnauthorized: () => void = () => {};
let refreshAccessToken: () => Promise<string | null> = async () => null;

/** 401 을 받았을 때 부를 함수. 세션 저장소가 등록한다(순환 import 를 피하려고 주입받는다). */
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

/** 토큰이 만료됐을 때 새 토큰을 받아 오는 함수. 회원이면 리프레시 쿠키로 받고, 게스트면 null 이다. */
export function setRefreshHandler(handler: () => Promise<string | null>): void {
  refreshAccessToken = handler;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
}

/**
 * 서버 오류 응답 {code, message} 를 ApiError 로 바꿔 던진다.
 * 토큰을 실은 요청이 401 을 받으면 한 번만 새 토큰을 받아 다시 보낸다(회원 액세스 토큰은 15분이면 만료된다).
 */
export async function api<T>(path: string, options: RequestOptions = {}, retried = false): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token) headers["Authorization"] = `Bearer ${options.token}`;

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && options.token && !retried) {
      const fresh = await refreshAccessToken();
      if (fresh) return api<T>(path, { ...options, token: fresh }, true);
    }
    if (response.status === 401) onUnauthorized();
    throw new ApiError(data?.code ?? "INTERNAL", data?.message ?? response.statusText, response.status);
  }
  return data as T;
}
