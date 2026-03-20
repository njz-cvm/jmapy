
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jmapy.capability.base import CapabilityType


class JMAPYError(Exception): ...

class CapabilityNotSupported(JMAPYError):
    capability: str
    msg: str

    def __init__(self, capability: CapabilityType[Any, Any] | str) -> None:
        self.capability = capability if isinstance(capability, str) else capability.URN
        self.msg = f"The server does not support the capability {self.capability}"

        super().__init__(self.msg)