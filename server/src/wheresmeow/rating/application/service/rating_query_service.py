from wheresmeow.rating.application.port.inbound import Profile, RankingEntry, RankingPage, RatingSummary
from wheresmeow.rating.application.port.outbound import BotRecordSource, PlayerDirectory, RatingReader
from wheresmeow.rating.domain.elo import INITIAL_RATING
from wheresmeow.shared.errors import InvalidInput

PAGE_SIZE = 20
MIN_RANKED_GAMES = 5  # 랭킹에는 회원이면서 레이팅 대국 5판 이상인 사람만 나온다(스펙 4.5)
RECENT_GAMES = 20


class RatingQueryService:
    """GetRankings·GetProfile 유스케이스 구현."""

    def __init__(self, reader: RatingReader, players: PlayerDirectory, bot_records: BotRecordSource) -> None:
        self._reader = reader
        self._players = players
        self._bot_records = bot_records

    def rankings(self, page: int) -> RankingPage:
        if page < 1:
            raise InvalidInput(f"쪽 번호는 1 이상이어야 합니다: {page}")
        total = self._reader.count_ranked(MIN_RANKED_GAMES)
        offset = (page - 1) * PAGE_SIZE
        rows = self._reader.ranked(MIN_RANKED_GAMES, offset, PAGE_SIZE)
        entries = [
            RankingEntry(
                offset + index + 1, r.player_id, r.nickname, r.skin,
                RatingSummary(r.rating, r.games, r.wins, r.losses, r.draws),
            )
            for index, r in enumerate(rows)
        ]
        return RankingPage(page, max(1, -(-total // PAGE_SIZE)), entries)

    def current_rating(self, player_id: str) -> int:
        summary = self._reader.summary_of(player_id)
        return summary.rating if summary else INITIAL_RATING

    def profile(self, player_id: str) -> Profile:
        card = self._players.card_of(player_id)
        summary = self._reader.summary_of(player_id) or RatingSummary(INITIAL_RATING, 0, 0, 0, 0)
        return Profile(
            player_id=card.player_id,
            nickname=card.nickname,
            kind=card.kind,
            skin=card.skin,
            rating=summary,
            ranked=card.kind == "MEMBER" and summary.games >= MIN_RANKED_GAMES,
            recent_games=self._reader.recent_games(player_id, RECENT_GAMES),
            bot_records=self._bot_records.bot_records(player_id),
        )
