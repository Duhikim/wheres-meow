from fakes import FakeClock
from persistence_support import migrated_database
from wheresmeow.account.adapter.outbound.persistence.sql_player_store import SqlPlayerStore
from wheresmeow.account.domain.player import Player, PlayerKind
from wheresmeow.game.adapter.outbound.persistence.sql_game_result_recorder import SqlGameResultRecorder
from wheresmeow.game.domain.board import Board
from wheresmeow.game.domain.game import Game, GameMode, Seat
from wheresmeow.rating.adapter.outbound.persistence.rating_contributor import RatingContributor
from wheresmeow.rating.adapter.outbound.persistence.sql_rating_reader import SqlRatingReader
from wheresmeow.rating.application.port.inbound import RatingSummary

CATS = frozenset({(0, 0), (3, 3)})


class Env:
    def __init__(self) -> None:
        self.database = migrated_database()
        self.clock = FakeClock(now_ms=1_000)
        self.players = SqlPlayerStore(self.database, self.clock)
        self.recorder = SqlGameResultRecorder(self.database, self.clock, contributors=[RatingContributor(self.clock)])
        self.reader = SqlRatingReader(self.database)
        self.seq = 0

    def player(self, player_id: str, kind: PlayerKind = PlayerKind.MEMBER, nickname: str | None = None) -> None:
        self.players.save(Player(player_id, kind, nickname or player_id, 16, 17))

    def play(self, winner: str, loser: str, mode: GameMode = GameMode.INVITE) -> None:
        self.seq += 1
        self.clock.advance(1_000)
        now = self.clock.now_ms()
        seats = (Seat(winner, winner, 16), Seat(loser, loser, 17))
        game = Game(f"g{self.seq}", mode, Board(4, CATS), seats, 0, now,
                    bot_difficulty="EASY" if mode is GameMode.BOT else None)
        game.reveal(winner, 0, 0, now_ms=now)
        game.forfeit(loser, now_ms=now)
        self.recorder.record(game)


class TestSqlRatingReader:
    class TestRanked:
        def test_성공_회원이면서_기준_판수_이상인_사람만_레이팅_순으로_센다(self):
            env = Env()
            for pid in ("a", "b"):
                env.player(pid)
            env.player("guest", PlayerKind.GUEST)
            for _ in range(3):
                env.play("a", "b")
                env.play("guest", "a")

            rows = env.reader.ranked(min_games=5, offset=0, limit=20)

            assert [r.player_id for r in rows] == ["a"]  # b 는 3판, guest 는 게스트
            assert env.reader.count_ranked(min_games=5) == 1
            assert (rows[0].games, rows[0].wins, rows[0].losses) == (6, 3, 3)

        def test_성공_레이팅이_높은_순서이고_offset_limit_를_따른다(self):
            env = Env()
            for pid in ("a", "b", "c"):
                env.player(pid)
            env.play("a", "b")
            env.play("a", "c")
            env.play("b", "c")

            rows = env.reader.ranked(min_games=1, offset=1, limit=1)

            assert [r.player_id for r in rows] == ["b"]
            assert env.reader.count_ranked(min_games=1) == 3

    class TestSummary:
        def test_성공_레이팅과_승패를_돌려준다(self):
            env = Env()
            env.player("a")
            env.player("b")
            env.play("a", "b")

            assert env.reader.summary_of("a") == RatingSummary(1016, 1, 1, 0, 0)
            assert env.reader.summary_of("nobody") is None

    class TestRecentGames:
        def test_성공_사람_간_대국을_최근_순으로_상대와_결과_레이팅_변화와_함께_돌려준다(self):
            env = Env()
            env.player("a")
            env.player("b", nickname="비냥")
            env.play("a", "b")
            env.play("b", "a", mode=GameMode.MATCH)
            env.play("a", "bot:EASY", mode=GameMode.BOT)

            games = env.reader.recent_games("a", limit=20)

            assert [g.game_id for g in games] == ["g2", "g1"]  # 컴퓨터 대전은 빠진다
            latest = games[0]
            assert (latest.mode, latest.opponent_id, latest.opponent_nickname) == ("MATCH", "b", "b")
            assert (latest.result, latest.my_score, latest.opponent_score) == ("LOSS", 0, 1)
            assert (latest.rating_before, latest.rating_after) == (1016, 999)
            assert games[1].result == "WIN"

        def test_성공_limit_개수만큼만_돌려준다(self):
            env = Env()
            env.player("a")
            env.player("b")
            for _ in range(3):
                env.play("a", "b")

            assert len(env.reader.recent_games("a", limit=2)) == 2
