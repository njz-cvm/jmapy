import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, Self

from jmapy.models import ID
from jmapy.orm.base import DictReference, ListReference, NullReference, Reference

from .base import (
    MethodCall,
    MethodChain,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,
)


class SetError:
    type = Reference[Self, str]()
    description = Reference[Self, str | None]()

class SetResponse[T](_DataType):
    account_id = Reference[Self, ID]()
    old_state= NullReference[Self, str | None]()
    new_state = Reference[Self, str]()
    created = DictReference[Self, T]()
    updated = DictReference[Self, T]()
    destroyed = ListReference[Self, ID]()
    not_created = DictReference[Self, SetError]()
    not_updated = DictReference[Self, SetError]()
    not_destroyed = DictReference[Self, SetError]()

class SettableData(Protocol):
    @classmethod
    def set(
        cls,
        account_id: ID | Reference[Any, ID],
        if_in_state: str | None | Reference[Any, str],
        create: Mapping[ID, Self] | None | Reference[Any, Mapping[ID, Self]] = None,
        update: Mapping[ID, Mapping[Reference[Self, Any] | Self, Any]] | None = None,
        destroy: Sequence[ID] | None = None,
    ) -> MethodChain[SetResponse[Self]]:
        method_name = f"{cls.__name__}/set"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **(bind_arg("ifInState", if_in_state) if if_in_state is not None else {}),
                        **(bind_arg("properties", properties) if properties else {})
                    },
                    call_id,
                    SetResponse
                )
            ]
        )

