
import uuid
from typing import TYPE_CHECKING, Any, Protocol, Self

from jmapy.models import ID

from .base import ListReference, MethodCall, MethodChain, Reference


class GetResponse[T]:
    account_id = Reference[Self, str]()
    state = Reference[Self, str]()
    list = ListReference[Self, T]()
    not_found = ListReference[Self, ID]()

    # Explicit constructor mappings for actual responses

    if not TYPE_CHECKING:

        def __init__(
            self,
            account_id: str = "",
            state: str = "",
            list: "list[T] | None" = None,
            not_found: "list[ID] | None" = None
        ) -> None:
            self.account_id = account_id
            self.state = state
            self.list = list if list is not None else []
            self.not_found = not_found if not_found is not None else []


class GettableData(Protocol):
    @classmethod
    def get(
        cls,
        account_id: ID | Reference[Any, ID],
        ids: list[ID] | ListReference[Any, ID] | Reference[Any, ID],
        properties: list[str] | None | ListReference[Any, str] | Reference[Any, str] = None,
    ) -> MethodChain[GetResponse[Self]]:
        method_name = f"{cls.__name__}/get"
        args: dict[str, Any] = {}

        def bind_arg(key: str, value: Any):
            # Check if this parameter is a lazy JMAP Result Reference
            if hasattr(value, "to_dict") and getattr(value, "result_of", None):
                args[f"#{key}"] = value.to_dict()
            elif hasattr(value, "to_dict"):
                args[key] = value.to_dict()
            else:
                args[key] = value

        bind_arg("accountId", account_id)
        bind_arg("ids", ids)
        if properties is not None:
            bind_arg("properties", properties)

        # Generate a unique client-side call ID for this method
        call_id = f"c_{uuid.uuid4().hex[:6]}"
        return MethodChain([MethodCall(method_name, args, call_id, GetResponse)])