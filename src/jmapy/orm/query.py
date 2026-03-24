from typing import Self

from jmapy.models import ID

from .base import ListReference, Reference


class QueryResponse:
    account_id = Reference[Self, ID]()
    query_state = Reference[Self, str]()
    can_calculate_changes = Reference[Self, bool]()
    position = Reference[Self, int]()
    ids = ListReference[Self, ID]()
    total = Reference[Self, int]()
    limit = Reference[Self, int]()