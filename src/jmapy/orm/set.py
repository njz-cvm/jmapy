from typing import Self

from jmapy.models import ID

from .base import ListReference, Reference


class SetResponse[T]:
    account_id: Reference["SetResponse[T]", str] = Reference()
    old_state: Reference["SetResponse[T]", str] = Reference()
    new_state: Reference["SetResponse[T]", str] = Reference()
    created: DictReference["SetResponse[T]", T] = DictReference()
    updated: DictReference["SetResponse[T]", T] = DictReference()
    destroyed: ListReference["SetResponse[T]", ID] = ListReference()
    not_created: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
    not_updated: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
    not_destroyed: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
