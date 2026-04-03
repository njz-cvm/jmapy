from typing import Any, Self

from jmapy.models import ID

from .base import (
    DEFAULT_ACCOUNT,
    ListReference,
    MethodCall,
    MethodChain,
    MethodResponse,
    Reference,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,
)


class ChangesResponse(_DataType):
    account_id = Reference[Self, ID](ID)
    old_state = Reference[Self, str](str)
    new_state = Reference[Self, str](str)
    has_more_changes = Reference[Self, bool](bool)
    created = ListReference[Self, ID](ID)
    updated = ListReference[Self, ID](ID)
    destroyed = ListReference[Self, ID](ID)

class ChangableData(MethodResponse):

    @classmethod
    def changes(
        cls,
        since_state: str | Reference[Any, str],
        max_changes: int | None | Reference[Any, int] = None,
        account_id: ID | Reference[Any, ID] | DEFAULT_ACCOUNT = DEFAULT_ACCOUNT(),
    ) -> MethodChain[ChangesResponse]:

        return MethodChain(
            [
                MethodCall(
                    f"{cls.__name__}/changes",
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("sinceState", since_state),
                        **(bind_arg("maxChanges", max_changes) if max_changes is not None else {})
                    },
                    cls.__new_call_id__(),
                    ChangesResponse,
                    None
                )
            ]
        )

