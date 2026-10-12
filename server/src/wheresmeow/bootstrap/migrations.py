"""서버 시작 시 DB 스키마를 최신으로 맞춘다. 스크립트는 패키지 안(wheresmeow/migrations)에 있어 운영 이미지에 함께 들어간다."""

from pathlib import Path

from alembic import command
from alembic.config import Config

import wheresmeow.migrations
from wheresmeow.shared.persistence.database import Database

MIGRATIONS_DIR = Path(wheresmeow.migrations.__file__).parent


def run_migrations(database: Database) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    with database.engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
