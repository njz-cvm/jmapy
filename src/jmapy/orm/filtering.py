
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(slots=True, frozen=True)
class FilterCondition:
    reference: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            self.reference: self.value
        }

@dataclass(slots=True, frozen=True)
class FilterOperator:
    operator: Literal["AND", "OR", "NOT"]
    conditions: "list[FilterOperator | FilterCondition]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "conditions": [cond.to_dict() for cond in self.conditions]
        }

type Filter = FilterCondition | FilterOperator

def _flatten_join(op: Literal["AND", "OR", "NOT"], *filters: Filter) -> FilterOperator:
    operator = FilterOperator(op, [])
    for filter in filters:
        if isinstance(filter, FilterOperator) and filter.operator == op:
            operator.conditions.extend(filter.conditions)
        else:
            operator.conditions.append(filter)
    return operator

def and_(*filters: Filter) -> FilterOperator:
    return _flatten_join("AND", *filters)

def or_(*filters: Filter) -> FilterOperator:
    return _flatten_join("OR", *filters)

def not_(*filters: Filter) -> FilterOperator:
    return _flatten_join("NOT", *filters)

@dataclass(slots=True, frozen=True)
class Comparator[T]:
    property: str
    is_ascending: bool | None = None
    collation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "property": self.property,
            **({"isAscending": self.is_ascending} if self.is_ascending is not None else {}),
            **({"collation": self.collation} if self.collation is not None else {})
        }

