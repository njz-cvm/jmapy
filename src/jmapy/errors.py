
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NamedTuple,
    Never,
    NotRequired,
    TypedDict,
)

if TYPE_CHECKING:
    from jmapy.capability.base import CapabilityType


class JMAPYError(Exception): ...

class JMAPYMethodError(JMAPYError):

    def __init__(self, type_: str, call_id: str, description: str | None = None) -> None:
        self.type = type_
        self.call_id = call_id
        self.description = description
        self.msg = f"Error during method call '{self.call_id}': {self.type}."
        if self.description:
            self.msg += f" The following information was included: '{self.description}'."
        super().__init__(self.msg)


class MethodError[T](NamedTuple):
    error: Literal["error"]
    details: T
    call_id: str

    def raise_on_error(self) -> Never:
        raise JMAPYMethodError(self.details["type"], self.call_id, self.details.get("description"))  # pyright: ignore[reportIndexIssue, reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]

    def is_error(self) -> Literal[True]:
        return True


class ServerUnavailable(TypedDict):
    type: Literal["serverUnavailable"]


class ServerFail(TypedDict):
    type: Literal["serverFail"]
    description: str


class ServerPartialFail(TypedDict):
    type: Literal["serverPartialFail"]


class UnknownMethod(TypedDict):
    type: Literal["unknownMethod"]


class InvalidArguments(TypedDict):
    type: Literal["invalidArguments"]
    description: NotRequired[str]


class InvalidResultReference(TypedDict):
    type: Literal["invalidResultReference"]


class Forbidden(TypedDict):
    type: Literal["forbidden"]


class AccountNotFound(TypedDict):
    type: Literal["accountNotFound"]


class AccountNotSupportedByMethod(TypedDict):
    type: Literal["accountNotSupportedByMethod"]


class AccountReadOnly(TypedDict):
    type: Literal["accountReadOnly"]


type GenericFailure = MethodError[
    ServerUnavailable |
    ServerFail |
    ServerPartialFail |
    UnknownMethod |
    InvalidArguments |
    InvalidResultReference |
    Forbidden |
    AccountNotFound |
    AccountNotSupportedByMethod |
    AccountReadOnly
]


class RequestTooLarge(TypedDict):
    type: Literal["requestTooLarge"]


type GetFailure = MethodError[
    RequestTooLarge
]


class CannotCalculateChanges(TypedDict):
    type: Literal["cannotCalculateChanges"]


type ChangesFailure = MethodError[
    CannotCalculateChanges
]


class StateMismatch(TypedDict):
    type: Literal["stateMismatch"]


type SetFailure = MethodError[
    RequestTooLarge |
    StateMismatch
]


class FromAccountNotValid(TypedDict):
    type: Literal["fromAccountNotFound"]


class FromAccountNotSupportedByMethod(TypedDict):
    type: Literal["fromAccountNotSupportedByMethod"]


type CopyFailure = MethodError[
    FromAccountNotValid |
    FromAccountNotSupportedByMethod |
    StateMismatch
]


class AnchorNotFound(TypedDict):
    type: Literal["anchorNotFound"]


class UnsupportedSort(TypedDict):
    type: Literal["unsupportedSort"]


class UnsupportedFilter(TypedDict):
    type: Literal["unsupportedFilter"]


type QueryFailure = MethodError[
    AnchorNotFound |
    UnsupportedSort |
    UnsupportedFilter
]


class TooManyChanges(TypedDict):
    type: Literal["tooManyChanges"]


type QueryChangesFailure = MethodError[
    TooManyChanges |
    CannotCalculateChanges
]


class CapabilityNotSupported(JMAPYError):
    capability: str
    msg: str

    def __init__(self, capability: "CapabilityType[Any, Any] | str") -> None:
        self.capability = capability if isinstance(capability, str) else capability.URN
        self.msg = f"The server does not support the capability {self.capability}"

        super().__init__(self.msg)