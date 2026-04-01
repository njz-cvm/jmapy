
import uuid
from collections.abc import Iterable
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import ListReference, Reference
from jmapy.orm.errors import CallError

from .base import (
    DEFAULT_ACCOUNT,
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


class TooManyIDs[T](CallError[GetResponse[T]]): ...


class GettableData:
    @classmethod
    def get(
        cls,
        ids: Iterable[ID] | ListReference[Any, ID] | Reference[Any, ID],
        properties: Iterable[str] | None | ListReference[Any, str] | Reference[Any, str] = None,
        account_id: ID | Reference[Any, ID] | DEFAULT_ACCOUNT = DEFAULT_ACCOUNT(),
    ) -> MethodChain[GetResponse[Self]]:
        method_name = f"{cls.__name__}/get"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain[GetResponse[Self]](
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("ids", ids),
                        **bind_arg("properties", properties)
                    },
                    call_id,
                    GetResponse,
                    None
                )
            ]
        )
