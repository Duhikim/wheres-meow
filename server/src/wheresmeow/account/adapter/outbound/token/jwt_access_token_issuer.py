import jwt

from wheresmeow.shared.clock import Clock
from wheresmeow.shared.errors import Unauthorized

ACCESS_TTL_MS = 15 * 60 * 1000
TOKEN_TYPE = "access"


class JwtAccessTokenIssuer:
    """회원 액세스 토큰. 15분짜리 HS256 JWT 이며 클라이언트는 메모리에만 둔다(스펙 4.4).

    만료는 주입받은 시계로 직접 확인한다(테스트에서 시간을 움직일 수 있게).
    """

    def __init__(self, secret_key: str, clock: Clock) -> None:
        if not secret_key:
            raise ValueError("서명 키가 비어 있습니다")
        self._secret = secret_key
        self._clock = clock

    def issue(self, player_id: str) -> str:
        now = self._clock.now_ms()
        claims = {"sub": player_id, "typ": TOKEN_TYPE, "iat": now // 1000, "exp_ms": now + ACCESS_TTL_MS}
        return jwt.encode(claims, self._secret, algorithm="HS256")

    def verify(self, token: str) -> str:
        try:
            claims = jwt.decode(token, self._secret, algorithms=["HS256"], options={"require": ["sub", "exp_ms"]})
        except jwt.PyJWTError as error:
            raise Unauthorized("유효하지 않은 액세스 토큰입니다") from error
        if claims.get("typ") != TOKEN_TYPE or self._clock.now_ms() >= claims["exp_ms"]:
            raise Unauthorized("만료되었거나 잘못된 액세스 토큰입니다")
        return claims["sub"]
