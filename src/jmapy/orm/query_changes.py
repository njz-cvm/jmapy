from typing import Self

from jmapy.models import ID

from .base import ListReference, Reference


class AddedItem:
    id = Reference[Self, ID]()
    index = Reference[Self, int]()

class QueryChangesResponse[T]:
    account_id = Reference[Self, ID]()
    old_query_state = Reference[Self, str]()
    new_query_state = Reference[Self, str]()
    total = Reference[Self, int]()
    removed = ListReference[Self, ID]()
    added = ListReference[Self, AddedItem]()