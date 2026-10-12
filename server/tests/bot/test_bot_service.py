import pytest

from wheresmeow.bot.application.port.outbound import HumanProfile
from wheresmeow.bot.application.service.bot_service import BOT_NICKNAMES, BotService
from wheresmeow.bot.domain.solver import Difficulty
from wheresmeow.shared.errors import InvalidInput


class FakeDirectory:
    def profile(self, player_id: str) -> HumanProfile:
        return HumanProfile(player_id, "사람냥", 9, 21)


class FakeStarter:
    def __init__(self) -> None:
        self.calls = []

    def start_bot_game(self, human: HumanProfile, difficulty: Difficulty, bot_nickname: str) -> str:
        self.calls.append((human, difficulty, bot_nickname))
        return "g1"


class FakeRecords:
    def records_of(self, player_id: str) -> dict:
        return {Difficulty.HARD: (2, 1, 0)}


class TestBotService:
    @pytest.fixture
    def env(self):
        starter = FakeStarter()
        return BotService(FakeDirectory(), starter, FakeRecords()), starter

    class TestStartBotGame:
        def test_성공_난이도에_맞는_이름으로_봇_대국을_시작한다(self, env):
            service, starter = env

            game_id = service.start_bot_game("p1", "HARD")

            assert game_id == "g1"
            human, difficulty, nickname = starter.calls[0]
            assert (human.player_id, difficulty, nickname) == ("p1", Difficulty.HARD, BOT_NICKNAMES[Difficulty.HARD])
            assert len(nickname) <= 12

        def test_실패_모르는_난이도면_INVALID_INPUT(self, env):
            service, starter = env

            with pytest.raises(InvalidInput):
                service.start_bot_game("p1", "IMPOSSIBLE")
            assert starter.calls == []

    class TestRecords:
        def test_성공_세_난이도를_모두_돌려주고_없는_기록은_0이다(self, env):
            service, _ = env

            records = service.bot_records("p1")

            assert records == [
                {"difficulty": "EASY", "wins": 0, "losses": 0, "draws": 0},
                {"difficulty": "NORMAL", "wins": 0, "losses": 0, "draws": 0},
                {"difficulty": "HARD", "wins": 2, "losses": 1, "draws": 0},
            ]
