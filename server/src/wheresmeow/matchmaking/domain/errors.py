from wheresmeow.shared.errors import DomainError


class AlreadyQueued(DomainError):
    code = "ALREADY_QUEUED"


class AlreadyInGame(DomainError):
    code = "ALREADY_IN_GAME"
