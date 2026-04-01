import string
from collections.abc import Callable
from typing import Annotated, Any, NamedTuple

from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationError,
)
from pydantic.alias_generators import to_camel

ID_ALLOWED_CHARS = string.ascii_lowercase = string.ascii_uppercase + "-_"

ID = Annotated[
    str,
    Field(min_length=1, max_length=255, pattern=f"[{ID_ALLOWED_CHARS}]*"),
]

def check_and_return(condition: Callable[[str], bool]):
    def check(string: str) -> str:
        if condition(string):
            return string
        msg = f"Condition failed when validating '{string}'"
        raise ValidationError(msg)
    return check

DownloadUrl = Annotated[
    str,
    AfterValidator(
        check_and_return(
                lambda string: all(
                f"{{{variable}}}" in string
                for variable in ("accountId", "blobId", "type", "name")
            )
        )
    )
]
UploadUrl = Annotated[
    str,
    AfterValidator(
        check_and_return(
            lambda string: all(
                f"{{{variable}}}" in string
                for variable in ("accountId",)
            )
        )
    )
]
EventSourceUrl = Annotated[
    str,
    AfterValidator(
        check_and_return(
            lambda string: all(
                f"{{{variable}}}" in string
                for variable in ("types", "closeafter", "ping")
            )
        )
    )
]

class Account(BaseModel):
    name: str
    is_personal: bool
    is_read_only: bool
    account_capabilities: dict[str, Any]

    model_config = {
        "alias_generator": to_camel
    }


class SessionResponse(BaseModel):
    capabilities: dict[str, Any]
    accounts: dict[ID, Account]
    primary_accounts: dict[str, ID]
    username: str
    api_url: str
    download_url: DownloadUrl
    upload_url: UploadUrl
    event_source_url: EventSourceUrl
    state: str

    model_config = {
        "alias_generator": to_camel
    }


class Invocation(NamedTuple):
    name: str
    data: dict[str, Any]
    call_id: str


class JMAPResponse(BaseModel):
    method_responses: list[Invocation]
    created_ids: dict[ID, ID] | None = None
    session_state: str

    model_config = {
        "alias_generator": to_camel
    }
