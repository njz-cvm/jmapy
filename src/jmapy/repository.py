
from enum import Enum
from typing import Protocol

from jmapy.models import ID


class DELETED(Enum): ...

class Cache[T](Protocol):
    FASTER_HAS: bool

    async def has(self, identity: str) -> bool: ...

    async def get(self, identity: str) -> T | None: ...

    async def update(self, changes: dict[ID, T | DELETED]) -> None: ...

class Repository[T](Protocol):
    MAX_STATE_HISTORY = 500

    cache: Cache[T]
    _state: str

    @property
    def state(self) -> str:
        return self._state

    async def update_state(self, state: str, changes: dict[ID, T | DELETED]) -> None:
        await self.cache.update(changes)
        self._state = state

    async def get(self, identity: str) -> T | None: ...

    async def is_cached(self, identity: str) -> bool:
        return await self.cache.has(identity)

    