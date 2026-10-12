"""inbound 어댑터가 요청 본문을 pydantic 스키마로 검증할 때 쓰는 도우미."""

from typing import Any

from pydantic import BaseModel, ValidationError

from wheresmeow.shared.errors import InvalidInput


def parse_payload[M: BaseModel](model: type[M], data: Any) -> M:
    try:
        return model.model_validate(data if data is not None else {})
    except ValidationError as error:
        raise InvalidInput(error.errors(include_url=False)[0]["msg"]) from error
