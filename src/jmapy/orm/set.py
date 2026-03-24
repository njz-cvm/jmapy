from typing import Self

from jmapy.models import ID

from .base import DictReference, ListReference, NullReference, Reference


class SetError:
    type = Reference[Self, str]()
    description = Reference[Self, str | None]()

class SetResponse[T]:
    account_id = Reference[Self, ID]()
    old_state = NullReference[Self, str]()
    new_state = Reference[Self, str]()
    created = DictReference[Self, T]()
    updated = DictReference[Self, T]()
    destroyed = ListReference[Self, ID]()
    not_created = DictReference[Self, SetError]()
    not_updated = DictReference[Self, SetError]()
    not_destroyed = DictReference[Self, SetError]()

SetResponse().old_state
