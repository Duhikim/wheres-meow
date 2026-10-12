from wheresmeow.bot.application.port.outbound import BotGameStarter, BotRecordReader, HumanDirectory
from wheresmeow.bot.domain.solver import Difficulty
from wheresmeow.shared.errors import InvalidInput

BOT_NICKNAMES = {
    Difficulty.EASY: "컴퓨터 (쉬움)",
    Difficulty.NORMAL: "컴퓨터 (보통)",
    Difficulty.HARD: "컴퓨터 (어려움)",
}


class BotService:
    """StartBotGame·BotRecords 유스케이스 구현."""

    def __init__(self, humans: HumanDirectory, starter: BotGameStarter, records: BotRecordReader) -> None:
        self._humans = humans
        self._starter = starter
        self._records = records

    def start_bot_game(self, player_id: str, difficulty: str) -> str:
        try:
            level = Difficulty(difficulty)
        except ValueError as error:
            raise InvalidInput(f"알 수 없는 난이도입니다: {difficulty}") from error
        return self._starter.start_bot_game(self._humans.profile(player_id), level, BOT_NICKNAMES[level])

    def bot_records(self, player_id: str) -> list[dict]:
        records = self._records.records_of(player_id)
        result = []
        for level in Difficulty:
            wins, losses, draws = records.get(level, (0, 0, 0))
            result.append({"difficulty": level.value, "wins": wins, "losses": losses, "draws": draws})
        return result
