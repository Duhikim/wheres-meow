def player_room(player_id: str) -> str:
    """플레이어의 모든 소켓 연결이 들어가는 Socket.IO 룸 이름. 탭을 여러 개 열어도 모두 받는다."""
    return f"player:{player_id}"
