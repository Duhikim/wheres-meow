"""모든 도메인의 ORM 모델을 불러와 Base.metadata 에 등록한다. 마이그레이션과 테스트가 이 모듈을 쓴다."""

from wheresmeow.account.adapter.outbound.persistence import models as account_models  # noqa: F401
from wheresmeow.game.adapter.outbound.persistence import models as game_models  # noqa: F401
from wheresmeow.shared.persistence.database import Base

__all__ = ["Base"]
