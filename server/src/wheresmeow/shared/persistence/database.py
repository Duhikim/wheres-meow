"""모든 도메인의 영속 어댑터가 함께 쓰는 DB 연결과 ORM 기반 클래스.

ORM 모델은 각 도메인의 adapter/outbound/persistence 에만 두고, 도메인 엔티티와는 매핑 함수로 변환한다.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    """Railway 등이 주는 postgres:// · postgresql:// 주소를 순수 Python 드라이버(pg8000) 주소로 바꾼다.

    pg8000 은 gevent 의 소켓 패치를 그대로 따르므로 DB 를 기다리는 동안 다른 요청을 막지 않는다.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+pg8000://" + url[len(prefix):]
    return url


def ms_to_datetime(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def datetime_to_ms(value: datetime) -> int:
    """SQLite 는 시간대를 버리고 돌려주므로, 시간대가 없으면 저장할 때 쓴 UTC 로 본다."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return round(value.timestamp() * 1000)


class Database:
    def __init__(self, url: str) -> None:
        self.url = normalize_database_url(url)
        options: dict = {}
        if self.url.startswith("sqlite"):
            options["connect_args"] = {"check_same_thread": False}
            if self.url in ("sqlite://", "sqlite:///:memory:"):
                options["poolclass"] = StaticPool  # 메모리 DB 는 연결 하나를 공유해야 같은 DB 를 본다
        else:
            options["pool_pre_ping"] = True
        self.engine = create_engine(self.url, **options)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Iterator[Session]:
        """블록이 정상 종료되면 커밋하고, 예외가 나면 롤백한 뒤 예외를 그대로 던진다."""
        session = self._sessions()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()
