import datetime
import uuid
from collections.abc import Iterable
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.filtering import Comparator, FilterCondition, FilterOperator

from .base import ListReference, MethodCall, MethodChain, Reference, bind_arg


class QueryResponse:
    account_id = Reference[Self, ID]()
    query_state = Reference[Self, str]()
    can_calculate_changes = Reference[Self, bool]()
    position = Reference[Self, int]()
    ids = ListReference[Self, ID]()
    total = Reference[Self, int]()
    limit = Reference[Self, int]()


class QueryableData:
    type QSortableReference = Reference[Self, str] | Reference[Self, int] | Reference[Self, bool] | Reference[Self, datetime.datetime]

    @classmethod
    def query(
        cls,
        account_id: ID | Reference[Any, ID],
        filter: FilterOperator | FilterCondition | None = None,
        sort: Iterable[Comparator[Self] | QSortableReference] | None = None,
        position: int | None = None,
        anchor: ID | None = None,
        anchor_offset: int | None = None,
        limit: int | None = None,
        calculate_total: bool | None = None,
    ) -> MethodChain[QueryResponse]:
        method_name = f"{cls.__name__}/query"
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
                        **bind_arg("position", position),
                        **bind_arg("anchor", anchor),
                        **bind_arg("anchorOffset", anchor_offset),
                        **bind_arg("limit", limit),
                        **bind_arg("calculateTotal", calculate_total),
                    },
                    call_id,
                    QueryResponse
                )
            ]
        )

