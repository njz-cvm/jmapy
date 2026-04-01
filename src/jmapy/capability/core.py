
import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import BaseModel
from pydantic.alias_generators import to_snake

from jmapy.models import ID
from jmapy.orm.base import (
    DataType,
    ListReference,
    MethodCall,
    MethodChain,
    NullDictReference,
    Reference,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,  # pyright: ignore[reportPrivateUsage]
)
from jmapy.orm.copy import CopyableData, CopyResponse
from jmapy.orm.set import SetError

if TYPE_CHECKING:
    from jmapy.session import JMAPSession

from .base import CapabilityType


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



class Core(DataType):

    @classmethod
    def echo[T](cls, data: dict[str, T]) -> MethodChain[dict[str, T]]:

        method_name = "Core/echo"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain[dict[str, T]](
            [
                MethodCall(
                    method_name,
                    data,
                    call_id,
                    dict[str, T]
                )
            ]
        )


class BlobCopyResponse(_DataType):
    from_account_id: Reference[Self, ID]
    account_id: Reference[Self, ID]
    copied: NullDictReference[Self, ID, ID]
    not_copied: NullDictReference[Self, ID, SetError]


class Blob(CopyableData, DataType):

    @classmethod
    def copy(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        from_account_id: ID | Reference[Any, ID],
        account_id: ID | Reference[Any, ID],
        blob_ids: list[ID] | ListReference[Any, ID],
    ) -> MethodChain[CopyResponse[Self]]:
        method_name = "Blob/copy"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("fromAccountId", from_account_id),
                        **bind_arg("accountId", account_id),
                        **bind_arg("blobIds", blob_ids),
                    },
                    call_id,
                    CopyResponse
                )
            ]
        )


class CoreCapability[S: JMAPSession](CapabilityType[S, CoreSessionSettings]):
    URN = "urn:ietf:params:jmap:core"
    SessionInformation = ClassVar[CoreSessionSettings]

    _state_token: str
    _settings: CoreSessionSettings

    def __init__(self, session: S) -> None:
        self.session = session
    

