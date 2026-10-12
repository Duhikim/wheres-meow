import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEV_SECRET_KEY = "dev-only-secret"


@dataclass(frozen=True)
class AppConfig:
    env: str = "development"  # development · test · production
    secret_key: str = DEV_SECRET_KEY
    test_seed: int | None = None
    async_mode: str = "threading"  # 운영은 gevent
    static_dir: str | None = None  # 빌드된 웹(web/dist) 폴더. 있으면 Flask 가 화면도 제공한다

    def __post_init__(self) -> None:
        if self.env not in ("development", "test", "production"):
            raise ValueError(f"알 수 없는 실행 환경입니다: {self.env}")
        if self.env == "production":
            if self.secret_key == DEV_SECRET_KEY or not self.secret_key:
                raise ValueError("운영 환경에는 WHERESMEOW_SECRET_KEY 가 필요합니다")
            if self.test_seed is not None:
                raise ValueError("운영 환경에서 WHERESMEOW_TEST_SEED 를 켤 수 없습니다")
            if self.async_mode != "gevent":
                raise ValueError("운영 환경은 WHERESMEOW_ASYNC_MODE=gevent 로 실행해야 합니다")
        if self.static_dir is not None and not (Path(self.static_dir) / "index.html").is_file():
            raise ValueError(f"정적 파일 폴더에 index.html 이 없습니다: {self.static_dir}")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "AppConfig":
        seed = environ.get("WHERESMEOW_TEST_SEED")
        return cls(
            env=environ.get("WHERESMEOW_ENV", "development"),
            secret_key=environ.get("WHERESMEOW_SECRET_KEY", DEV_SECRET_KEY),
            test_seed=int(seed) if seed else None,
            async_mode=environ.get("WHERESMEOW_ASYNC_MODE", "threading"),
            static_dir=environ.get("WHERESMEOW_STATIC_DIR") or None,
        )
