"""DB 를 쓰는 테스트 공용 도우미. 메모리 SQLite 에 실제 마이그레이션을 적용해 쓴다."""

from wheresmeow.bootstrap.migrations import run_migrations
from wheresmeow.shared.persistence.database import Database


def migrated_database() -> Database:
    database = Database("sqlite://")
    run_migrations(database)
    return database
