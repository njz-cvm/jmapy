import datetime
import uuid
from collections.abc import Iterable
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.filtering import Comparator, FilterCondition, FilterOperator

from .base import (
    DEFAULT_ACCOUNT,
    ListReference,
    MethodCall,
    MethodChain,
    Reference,
    bind_arg,
)


class AddedItem:
    id = Reference[Self, ID](ID)
    index = Reference[Self, int](int)

class QueryChangesResponse[T]:
    account_id = Reference[Self, ID](ID)
    old_query_state = Reference[Self, str](str)
    new_query_state = Reference[Self, str](str)
    total = Reference[Self, int](int)
    removed = ListReference[Self, ID](ID)
    added = ListReference[Self, AddedItem](AddedItem)



class QueryChangableData:
    type QCSortableReference = Reference[Self, str] | Reference[Self, int] | Reference[Self, bool] | Reference[Self, datetime.datetime]

    @classmethod
    def query_changes(
        cls,
        since_query_state: str,
        filter: FilterOperator | FilterCondition | None = None,
        sort: Iterable[Comparator[Self] | QCSortableReference] | None = None,
        max_changes: int | None = None,
        up_to_id: ID | None = None,
        calculate_total: bool | None = None,
        account_id: ID | Reference[Any, ID] | DEFAULT_ACCOUNT = DEFAULT_ACCOUNT(),
    ) -> MethodChain[QueryChangesResponse[Self]]:
        method_name = f"{cls.__name__}/queryChanges"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        if sort is not None:
            resolved_sort = [  # pyright: ignore[reportUnknownVariableType]
                (item if isinstance(item, Comparator) else Comparator(item.attr_name))
                for item in sort
            ]
        else:
            resolved_sort = None

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("accountId", account_id),
                        **bind_arg("filter", filter),
                        **bind_arg("sort", resolved_sort),
                        **bind_arg("sinceQueryState", since_query_state),
                        **bind_arg("maxChanges", max_changes),
                        **bind_arg("upToId", up_to_id),
                        **bind_arg("calculateTotal", calculate_total),
                    },
                    call_id,
                    QueryChangesResponse[cls],
                    None
                )
            ]
        )


