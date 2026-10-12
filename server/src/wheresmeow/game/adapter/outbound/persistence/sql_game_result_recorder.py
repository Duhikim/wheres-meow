from collections.abc import Sequence
from typing import Protocol

from sqlalchemy.orm import Session

from wheresmeow.game.adapter.outbound.persistence.models import GameRecordRow
from wheresmeow.game.domain.game import Game
from wheresmeow.shared.clock import Clock
from wheresmeow.shared.persistence.database import Database, ms_to_datetime


class ResultContributor(Protocol):
    """대국 기록과 같은 트랜잭션에서 함께 갱신할 것(봇 전적, 레이팅 등). 실패하면 기록 전체가 롤백된다."""

    def contribute(self, session: Session, game: Game) -> None: ...


class SqlGameResultRecorder:
    """GameResultRecorder 포트의 DB 구현. 끝난 대국 하나를 game_records 에 한 줄로 남긴다."""

    def __init__(self, database: Database, clock: Clock, contributors: Sequence[ResultContributor] = ()) -> None:
        self._database = database
        self._clock = clock
        self._contributors = list(contributors)

    def record(self, game: Game) -> None:
        if game.end_reason is None:
            raise ValueError(f"끝나지 않은 대국은 기록할 수 없습니다: {game.id}")
        first, second = game.seats
        row = GameRecordRow(
            id=game.id,
            mode=game.mode.value,
            bot_difficulty=game.bot_difficulty,
            seat0_player_id=first.player_id,
            seat0_nickname=first.nickname,
            seat0_skin=first.skin,
            seat0_score=first.score,
            seat1_player_id=second.player_id,
            seat1_nickname=second.nickname,
            seat1_skin=second.skin,
            seat1_score=second.score,
            winner_seat=game.winner,
            end_reason=game.end_reason.value,
            cats=[[x, y] for x, y in sorted(game.board.cats)],
            moves=list(game.moves),
            started_at=ms_to_datetime(game.started_at_ms),
            ended_at=ms_to_datetime(self._clock.now_ms()),
        )
        with self._database.session() as session:
            session.add(row)
            for contributor in self._contributors:
                contributor.contribute(session, game)
