
from typing import TYPE_CHECKING, ClassVar, Protocol

from pydantic import BaseModel

if TYPE_CHECKING:
    from jmapy.session import JMAPSession


class CapabilityType[S: JMAPSession, B: BaseModel](Protocol):
    URN: ClassVar[str]
    SessionInformation: ClassVar[type[BaseModel]]

    session: S

    def __init__(
        self,
        session: S,
    ) -> None: ...

    @property
    def settings(self) -> B:
        return self.session.setting(self.URN, self.SessionInformation)  # pyright: ignore[reportReturnType]