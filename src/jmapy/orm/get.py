
import uuid
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import ListReference, Reference

from .base import (
    MethodCall,
    MethodChain,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,
)


class GetResponse[T](_DataType):
    account_id = Reference[Self, str]()
    state = Reference[Self, str]()
    list = ListReference[Self, T]()
    not_found = ListReference[Self, ID]()


class GettableData:
    @classmethod
    def get(
        cls,
        account_id: ID | Reference[Any, ID],
        ids: list[ID] | ListReference[Any, ID] | Reference[Any, ID],
        properties: list[str] | None | ListReference[Any, str] | Reference[Any, str] = None,
    ) -> MethodChain[GetResponse[Self]]:
        method_name = f"{cls.__name__}/get"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("ids", ids),
                        **(bind_arg("properties", properties) if properties else {})
                    },
                    call_id,
                    GetResponse
                )
            ]
        )
