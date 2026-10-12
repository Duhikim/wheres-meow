import pytest
from sqlalchemy import text

from wheresmeow.shared.persistence.database import Database, normalize_database_url


class TestNormalizeDatabaseUrl:
    class TestNormalize:
        @pytest.mark.parametrize(
            ("raw", "expected"),
            [
                ("postgres://u:p@h:5432/db", "postgresql+pg8000://u:p@h:5432/db"),
                ("postgresql://u:p@h/db", "postgresql+pg8000://u:p@h/db"),
                ("postgresql+pg8000://u:p@h/db", "postgresql+pg8000://u:p@h/db"),
                ("sqlite://", "sqlite://"),
            ],
        )
        def test_성공_Railway_형식_주소를_pg8000_드라이버_주소로_바꾼다(self, raw, expected):
            assert normalize_database_url(raw) == expected


class TestDatabase:
    class TestSession:
        def test_성공_블록이_끝나면_커밋한다(self):
            db = Database("sqlite://")
            with db.session() as s:
                s.execute(text("create table t (v int)"))
                s.execute(text("insert into t values (1)"))

            with db.session() as s:
                assert s.execute(text("select count(*) from t")).scalar() == 1

        def test_실패_예외가_나면_롤백하고_예외를_다시_던진다(self):
            db = Database("sqlite://")
            with db.session() as s:
                s.execute(text("create table t (v int)"))

            with pytest.raises(RuntimeError):
                with db.session() as s:
                    s.execute(text("insert into t values (1)"))
                    raise RuntimeError("boom")

            with db.session() as s:
                assert s.execute(text("select count(*) from t")).scalar() == 0
