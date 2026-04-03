
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import Reference

from .base import (
    DictReference,
    MethodCall,
    MethodChain,
    MethodResponse,
    NullDictReference,
    NullReference,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,
)


class CopyResponse[T](_DataType):
    from_account_id = Reference[Self, str](str)
    account_id = Reference[Self, str](str)
    old_state = NullReference[Self, str](str)
    new_state = Reference[Self, str](str)
    created = NullDictReference[Self, ID, T](ID, T)
    not_created = NullDictReference[Self, ID, object](ID, object)  # TODO: Add this error


class CopyableData(MethodResponse):

    @classmethod
    def copy(
        cls,
        from_account_id: ID | Reference[Any, ID],
        account_id: ID | Reference[Any, ID],
        create: dict[ID, Self] | DictReference[Self, ID, Self],
        if_from_in_state: str | Reference[Any, str] | None = None,
        if_in_state: str | Reference[Any, str] | None = None,
        on_success_destroy_original: bool | Reference[Any, bool] | None = None,
        destroy_from_if_in_state: str | Reference[Any, str] | None = None,
    ) -> MethodChain[CopyResponse[Self]]:

        return MethodChain(
            [
                MethodCall(
                    f"{cls.__name__}/copy",
                    {
                        **bind_arg("fromAccountId", from_account_id),
                        **bind_arg("ifFromInState", if_from_in_state),
                        **bind_arg("accountId", account_id),
                        **bind_arg("ifInState", if_in_state),
                        **bind_arg("create", create),
                        **bind_arg("onSuccessDestroyOriginal", on_success_destroy_original),
                        **bind_arg("destroyFromIfInState", destroy_from_if_in_state),
                    },
                    cls.__new_call_id__(),
                    CopyResponse[cls],
                    None
                )
            ]
        )
