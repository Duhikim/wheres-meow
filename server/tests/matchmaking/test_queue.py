from wheresmeow.matchmaking.domain.queue import Ticket, find_pairs, rating_window

T0 = 1_000_000


def ticket(player_id: str, rating: int, joined_after_s: float = 0) -> Ticket:
    return Ticket(player_id, rating, T0 + int(joined_after_s * 1000))


class TestRatingWindow:
    class TestWidening:
        def test_성공_처음엔_100이고_5초마다_50씩_넓어진다(self):
            t = ticket("a", 1000)

            assert rating_window(t, T0) == 100
            assert rating_window(t, T0 + 4_999) == 100
            assert rating_window(t, T0 + 5_000) == 150
            assert rating_window(t, T0 + 12_000) == 200

        def test_성공_30초가_지나면_제한이_없다(self):
            assert rating_window(ticket("a", 1000), T0 + 30_000) is None


class TestFindPairs:
    class TestPairing:
        def test_성공_레이팅_차이가_범위_안이면_짝짓고_먼저_온_사람이_앞이다(self):
            pairs = find_pairs([ticket("a", 1000), ticket("b", 1080, 1)], now_ms=T0 + 1_000)

            assert [(p.first.player_id, p.second.player_id) for p in pairs] == [("a", "b")]

        def test_성공_범위_밖이면_짝짓지_않는다(self):
            assert find_pairs([ticket("a", 1000), ticket("b", 1200)], now_ms=T0) == []

        def test_성공_기다리면_범위가_넓어져_짝지어진다(self):
            tickets = [ticket("a", 1000), ticket("b", 1200)]

            assert find_pairs(tickets, now_ms=T0 + 10_000)  # 두 사람 모두 ±200

        def test_성공_한쪽만_넓어졌으면_아직_짝짓지_않는다(self):
            tickets = [ticket("a", 1000), ticket("b", 1180, 9)]  # b 는 막 들어와 ±100

            assert find_pairs(tickets, now_ms=T0 + 10_000) == []

        def test_성공_30초가_지나면_레이팅과_관계없이_짝짓는다(self):
            tickets = [ticket("a", 800), ticket("b", 1900)]

            assert len(find_pairs(tickets, now_ms=T0 + 30_000)) == 1

        def test_성공_가장_가까운_레이팅과_짝짓고_한_사람은_한_번만_배정한다(self):
            tickets = [ticket("a", 1000), ticket("b", 1090, 1), ticket("c", 1010, 2), ticket("d", 1095, 3)]

            pairs = find_pairs(tickets, now_ms=T0 + 3_000)

            assert {(p.first.player_id, p.second.player_id) for p in pairs} == {("a", "c"), ("b", "d")}
            ids = [pid for p in pairs for pid in (p.first.player_id, p.second.player_id)]
            assert len(ids) == len(set(ids))

        def test_성공_혼자면_짝이_없다(self):
            assert find_pairs([ticket("a", 1000)], now_ms=T0 + 60_000) == []
