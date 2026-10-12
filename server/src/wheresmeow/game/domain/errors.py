from wheresmeow.shared.errors import DomainError


class NotYourTurn(DomainError):
    code = "NOT_YOUR_TURN"


class CellAlreadyOpen(DomainError):
    code = "CELL_ALREADY_OPEN"


class OutOfBoard(DomainError):
    code = "OUT_OF_BOARD"


class GameFinished(DomainError):
    code = "GAME_FINISHED"


class GameNotFound(DomainError):
    code = "GAME_NOT_FOUND"


class NotAParticipant(DomainError):
    code = "NOT_A_PARTICIPANT"


class AlreadyInGame(DomainError):
    code = "ALREADY_IN_GAME"


class InvalidSkin(DomainError):
    code = "INVALID_SKIN"
