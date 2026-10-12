from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from persistence_support import migrated_database
from wheresmeow.bootstrap.orm_models import Base


class TestMigrations:
    class TestUpgrade:
        def test_성공_필요한_테이블을_모두_만든다(self):
            database = migrated_database()

            tables = set(inspect(database.engine).get_table_names())

            assert {"players", "game_records", "bot_records", "ratings", "rating_changes", "single_records", "alembic_version"} <= tables

        def test_성공_마이그레이션_결과가_ORM_모델과_일치한다(self):
            database = migrated_database()

            with database.engine.connect() as connection:
                diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)

            assert diff == []

        def test_성공_두_번_적용해도_오류가_없다(self):
            from wheresmeow.bootstrap.migrations import run_migrations

            database = migrated_database()

            run_migrations(database)  # 이미 최신이면 아무것도 하지 않는다
