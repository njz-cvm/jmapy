
from typing import ClassVar

from pydantic import BaseModel
from pydantic.alias_generators import to_snake

from jmapy.capability.base import CapabilityType
from jmapy.session import JMAPSession


class CoreSessionSettings(BaseModel):
    max_size_upload: int
    max_concurrent_upload: int
    max_size_request: int
    max_concurrent_requests: int
    max_calls_in_request: int
    max_objects_in_get: int
    max_objects_in_set: int
    collation_algorithms: list[str]

    model_config = {
        "alias_generator": to_snake
    }


class CoreCapability[S: JMAPSession](CapabilityType[S, CoreSessionSettings]):
    URN = "urn:ietf:params:jmap:core"
    SessionInformation = ClassVar[CoreSessionSettings]

    _state_token: str
    _settings: CoreSessionSettings

    def __init__(self, session: S) -> None:
        self.session = session
    

