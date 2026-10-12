import pytest

from wheresmeow.rating.application.port.inbound import RatingSummary, RecentGame
from wheresmeow.rating.application.port.outbound import PlayerCard, RankedRow
from wheresmeow.rating.application.service.rating_query_service import (
    MIN_RANKED_GAMES,
    PAGE_SIZE,
    RatingQueryService,
)
from wheresmeow.shared.errors import InvalidInput


class FakeRatingReader:
    def __init__(self, ranked: list[RankedRow] | None = None) -> None:
        self.ranked_rows = ranked or []
        self.summaries: dict[str, RatingSummary] = {}
        self.recent: dict[str, list[RecentGame]] = {}
        self.calls: list = []

    def count_ranked(self, min_games: int) -> int:
        return len(self.ranked_rows)

    def ranked(self, min_games: int, offset: int, limit: int) -> list[RankedRow]:
        self.calls.append((min_games, offset, limit))
        return self.ranked_rows[offset:offset + limit]

    def summary_of(self, player_id: str) -> RatingSummary | None:
        return self.summaries.get(player_id)

    def recent_games(self, player_id: str, limit: int) -> list[RecentGame]:
        return self.recent.get(player_id, [])[:limit]


class FakePlayers:
    def __init__(self, *cards: PlayerCard) -> None:
        self.cards = {c.player_id: c for c in cards}

    def card_of(self, player_id: str) -> PlayerCard:
        return self.cards[player_id]


class FakeBotRecords:
    def bot_records(self, player_id: str) -> list[dict]:
        return [{"difficulty": "EASY", "wins": 1, "losses": 0, "draws": 0}]


class FakeSingleRecords:
    def single_records(self, player_id: str) -> list[dict]:
        return [{"difficulty": "BEGINNER", "bestMs": 41_000, "clears": 2}]


def row(n: int) -> RankedRow:
    return RankedRow(f"p{n}", f"냥{n}", 16, 1500 - n, 5, 3, 2, 0)


def service(reader=None, players=None) -> RatingQueryService:
    return RatingQueryService(reader or FakeRatingReader(), players or FakePlayers(), FakeBotRecords(), FakeSingleRecords())


class TestRatingQueryService:
    class TestRankings:
        def test_성공_회원_5판_이상만_한_쪽에_20명씩_순위를_매겨_보여준다(self):
            reader = FakeRatingReader([row(n) for n in range(45)])

            page = service(reader).rankings(page=2)

            assert reader.calls == [(MIN_RANKED_GAMES, PAGE_SIZE, PAGE_SIZE)]
            assert (page.page, page.total_pages) == (2, 3)
            assert [e.rank for e in page.entries][:2] == [21, 22]
            assert page.entries[0].nickname == "냥20"

        def test_성공_아무도_없으면_빈_첫_쪽이다(self):
            page = service().rankings(page=1)

            assert (page.page, page.total_pages, page.entries) == (1, 1, [])

        @pytest.mark.parametrize("bad", [0, -1])
        def test_실패_쪽_번호가_1보다_작으면_거부한다(self, bad):
            with pytest.raises(InvalidInput):
                service().rankings(page=bad)

    class TestProfile:
        def test_성공_레이팅_전적_최근_대국_봇_전적을_모은다(self):
            reader = FakeRatingReader()
            reader.summaries["m"] = RatingSummary(1100, 6, 4, 2, 0)
            recent = RecentGame("g1", "MATCH", 1_000, "o", "상대", 5, 3, "WIN", 1084, 1100)
            reader.recent["m"] = [recent]
            players = FakePlayers(PlayerCard("m", "회원냥", "MEMBER", 18))

            profile = service(reader, players).profile("m")

            assert (profile.nickname, profile.kind, profile.skin) == ("회원냥", "MEMBER", 18)
            assert profile.rating == RatingSummary(1100, 6, 4, 2, 0)
            assert profile.ranked is True
            assert profile.recent_games == [recent]
            assert profile.bot_records[0]["difficulty"] == "EASY"
            assert profile.single_records[0]["bestMs"] == 41_000

        def test_성공_대국이_없으면_초기_레이팅_1000이고_랭킹에_없다(self):
            players = FakePlayers(PlayerCard("g", "손님", "GUEST", 16))

            profile = service(players=players).profile("g")

            assert profile.rating == RatingSummary(1000, 0, 0, 0, 0)
            assert profile.ranked is False

        def test_성공_게스트는_5판_이상이어도_랭킹에_없다(self):
            reader = FakeRatingReader()
            reader.summaries["g"] = RatingSummary(1200, 9, 9, 0, 0)
            players = FakePlayers(PlayerCard("g", "손님", "GUEST", 16))

            assert service(reader, players).profile("g").ranked is False

    class TestCurrentRating:
        def test_성공_저장된_레이팅을_돌려준다(self):
            reader = FakeRatingReader()
            reader.summaries["m"] = RatingSummary(1234, 1, 1, 0, 0)

            assert service(reader).current_rating("m") == 1234

        def test_성공_대국이_없으면_초기_레이팅이다(self):
            assert service().current_rating("new") == 1000
