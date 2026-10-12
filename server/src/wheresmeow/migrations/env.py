"""Alembic 실행 환경. run_migrations() 가 넘겨 준 연결로만 동작한다(alembic.ini 를 쓰지 않는다)."""

from alembic import context

from wheresmeow.bootstrap.orm_models import Base

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("wheresmeow.bootstrap.migrations.run_migrations() 로 실행해야 합니다")

context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
