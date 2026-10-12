from itsdangerous import BadSignature, URLSafeTimedSerializer

from wheresmeow.shared.errors import Unauthorized

GUEST_TOKEN_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


class SignedTokenIssuer:
    """게스트 토큰. 서버 비밀 키로 서명한 player_id 이며 30일 뒤 만료된다."""

    def __init__(self, secret_key: str, max_age_seconds: int = GUEST_TOKEN_MAX_AGE_SECONDS) -> None:
        if not secret_key:
            raise ValueError("서명 키가 비어 있습니다")
        self._serializer = URLSafeTimedSerializer(secret_key, salt="wheresmeow-guest")
        self._max_age = max_age_seconds

    def issue(self, player_id: str) -> str:
        return self._serializer.dumps(player_id)

    def verify(self, token: str) -> str:
        try:
            # SignatureExpired 는 BadSignature 의 하위 클래스다
            return self._serializer.loads(token, max_age=self._max_age)
        except BadSignature as error:
            raise Unauthorized("유효하지 않은 토큰입니다") from error
