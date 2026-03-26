import uuid
from typing import Any, Self

from jmapy.models import ID

from .base import (
    ListReference,
    MethodCall,
    MethodChain,
    Reference,
    bind_arg,
)


class ChangesResponse:
    account_id = Reference[Self, ID]()
    old_state = Reference[Self, str]()
    new_state = Reference[Self, str]()
    has_more_changes = Reference[Self, bool]()
    created = ListReference[Self, ID]()
    updated = ListReference[Self, ID]()
    destroyed = ListReference[Self, ID]()

class ChangableData:
    @classmethod
    def changes(
        cls,
        account_id: ID | Reference[Any, ID],
        since_state: str | Reference[Any, str],
        max_changes: int | None | Reference[Any, int] = None,
    ) -> MethodChain[ChangesResponse]:
        method_name = f"{cls.__name__}/changes"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("sinceState", since_state),
                        **(bind_arg("maxChanges", max_changes) if max_changes is not None else {})
                    },
                    call_id,
                    ChangesResponse
                )
            ]
        )

