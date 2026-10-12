from collections.abc import Callable


class SingleRecordSourceAdapter:
    """rating 의 SingleRecordSource 포트를 practice 의 SingleRecords 유스케이스로 구현한다."""

    def __init__(self, single_records: Callable[[str], list[dict]]) -> None:
        self._single_records = single_records

    def single_records(self, player_id: str) -> list[dict]:
        return self._single_records(player_id)
