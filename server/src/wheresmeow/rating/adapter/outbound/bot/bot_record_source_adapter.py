from collections.abc import Callable


class BotRecordSourceAdapter:
    """rating 의 BotRecordSource 포트를 bot 의 BotRecords 유스케이스로 구현한다."""

    def __init__(self, bot_records: Callable[[str], list[dict]]) -> None:
        self._bot_records = bot_records

    def bot_records(self, player_id: str) -> list[dict]:
        return self._bot_records(player_id)
