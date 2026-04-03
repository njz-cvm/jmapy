
from collections.abc import Sequence
from typing import TYPE_CHECKING, AsyncContextManager, ClassVar, Protocol

from pydantic import BaseModel

from jmapy.orm.base import DataType

if TYPE_CHECKING:
    from jmapy.session import JMAPSession


class CapabilityType[S: JMAPSession, B: BaseModel](Protocol):
    URN: ClassVar[str]
    DATA_TYPES: Sequence[type[DataType]]
    SessionInformation: ClassVar[type[BaseModel]]

    session: S

    def __init__(
        self,
        session: S,
    ) -> None: ...

    @property
    def settings(self) -> B:
        return self.session.setting(self.URN, self.SessionInformation)  # pyright: ignore[reportReturnType]

    def lifespan(self) -> AsyncContextManager[None]: ...
