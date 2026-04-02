import uuid
from collections.abc import Iterable, Mapping
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import DictReference, ListReference, NullReference, Reference

from .base import (
    DEFAULT_ACCOUNT,
    MethodCall,
    MethodChain,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,
)


class SetError(_DataType):
    type = Reference[Self, str](str)
    description = Reference[Self, str | None](str | None)

class SetResponse[T](_DataType):
    account_id = Reference[Self, ID](ID)
    old_state= NullReference[Self, str | None](str | None)
    new_state = Reference[Self, str](str)
    created = DictReference[Self, ID, T](ID, T)
    updated = DictReference[Self, ID, T](ID, T)
    destroyed = ListReference[Self, ID](ID)
    not_created = DictReference[Self, ID, SetError](ID, SetError)
    not_updated = DictReference[Self, ID, SetError](ID, SetError)
    not_destroyed = DictReference[Self, ID, SetError](ID, SetError)

class SettableData:
    @classmethod
    def set(
        cls,
        if_in_state: str | None | Reference[Any, str] = None,
        create: Mapping[ID, Self] | None | DictReference[Any, ID, Self] = None,
        update: Mapping[ID, Mapping[Reference[Self, Any] | ListReference[Self, Any] | DictReference[Self, Any, Any], Any]] | None = None,
        destroy: Iterable[ID] | None | ListReference[Any, ID] = None,
        account_id: ID | Reference[Any, ID] | DEFAULT_ACCOUNT = DEFAULT_ACCOUNT(),
    ) -> MethodChain[SetResponse[Self]]:
        method_name = f"{cls.__name__}/set"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        if isinstance(update, Mapping):
            resolved_updates = {
                id: {
                    item_name.path.lstrip("/"): item_value
                    for item_name, item_value in updates.items()
                }
                for id, updates in update.items()
            }
        else:
            resolved_updates = update

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("ifInState", if_in_state),
                        **bind_arg("create", create),
                        **bind_arg("update", resolved_updates),
                        **bind_arg("destroy", destroy),
                    },
                    call_id,
                    SetResponse[cls],
                    None
                )
            ]
        )

