from typing import Self

from jmapy.models import ID

from .base import ListReference, Reference


class ChangesResponse:
    account_id = Reference[Self, ID]()
    old_state = Reference[Self, str]()
    new_state = Reference[Self, str]()
    has_more_changes = Reference[Self, bool]()
    created = ListReference[Self, ID]()
    updated = ListReference[Self, ID]()
    destroyed = ListReference[Self, ID]()
