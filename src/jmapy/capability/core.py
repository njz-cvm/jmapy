
import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from jmapy.models import ID, JMAPResponse
from jmapy.orm.base import (
    DataType,
    ListReference,
    MethodCall,
    MethodChain,
    NullDictReference,
    Reference,
    _DataType,  # pyright: ignore[reportPrivateUsage]
    bind_arg,  # pyright: ignore[reportPrivateUsage]
)
from jmapy.orm.copy import CopyableData, CopyResponse
from jmapy.orm.set import SetError

if TYPE_CHECKING:
    from jmapy.session import JMAPSession

from .base import CapabilityType


class CoreSessionSettings(BaseModel):
    max_size_upload: int
    max_concurrent_upload: int
    max_size_request: int
    max_concurrent_requests: int
    max_calls_in_request: int
    max_objects_in_get: int
    max_objects_in_set: int
    collation_algorithms: list[str]

    model_config = {
        "alias_generator": to_camel
    }



class Core(DataType):

    @classmethod
    def echo[T](cls, data: dict[str, T]) -> MethodChain[dict[str, T]]:

        method_name = "Core/echo"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain[dict[str, T]](
            [
                MethodCall(
                    method_name,
                    data,
                    call_id,
                    dict[str, T],
                    None
                )
            ]
        )


class BlobCopyResponse(_DataType):
    from_account_id: Reference[Self, ID]
    account_id: Reference[Self, ID]
    copied: NullDictReference[Self, ID, ID]
    not_copied: NullDictReference[Self, ID, SetError]


class Blob(CopyableData, DataType):

    @classmethod
    def copy(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        from_account_id: ID | Reference[Any, ID],
        account_id: ID | Reference[Any, ID],
        blob_ids: list[ID] | ListReference[Any, ID],
    ) -> MethodChain[CopyResponse[Self]]:
        method_name = f"{cls.__name__}/copy"
        call_id = f"c_{uuid.uuid4().hex[:6]}"

        return MethodChain(
            [
                MethodCall(
                    method_name,
                    {
                        **bind_arg("fromAccountId", from_account_id),
                        **bind_arg("accountId", account_id),
                        **bind_arg("blobIds", blob_ids),
                    },
                    call_id,
                    CopyResponse,
                    None
                )
            ]
        )


class CoreCapability[S: JMAPSession](CapabilityType[S, CoreSessionSettings]):
    INTERNAL_WORKER_CAP: int = 20
    URN = "urn:ietf:params:jmap:core"
    DATA_TYPES = [Blob, Core]
    SessionInformation = CoreSessionSettings

    _state_token: str
    _backlog: asyncio.Queue[tuple[MethodChain[Any, Any], asyncio.Future[JMAPResponse]]]
    _workers_stops: set[asyncio.Event]
    _workers: set[asyncio.Task[None]]

    def __init__(self, session: S) -> None:
        self.session = session
        self._backlog = asyncio.Queue()
        self._workers = set()
        self._workers_stops = set()

    async def _add_worker(self, index: int):
        stop_signal = asyncio.Event()
        worker_task = asyncio.create_task(
            self._core_worker(stop_signal),
            name = f"jmapy_core_{index}"
        )
        self._workers_stops.add(stop_signal)
        self._workers.add(worker_task)

    async def update_settings(self) -> None:
        worker_count = len(self._workers_stops)

        if self.settings.max_concurrent_requests > worker_count:
            for i in range(worker_count, self.settings.max_concurrent_requests):
                await self._add_worker(i)
            return

        diff = worker_count - self.settings.max_concurrent_requests

        for _, signal in zip(range(diff), self._workers_stops):
            signal.set()
        
        finished = 0
        while finished < diff:
            ended, _ = await asyncio.wait(self._workers, return_when=asyncio.FIRST_COMPLETED)
            finished += len(ended)
            _ = [self._workers.remove(t) for t in ended]

    async def make_request(self, methods: MethodChain[Any, Any]) -> JMAPResponse:
        jmap_future = asyncio.Future[JMAPResponse]()
        await self._backlog.put((methods, jmap_future))
        return await jmap_future

    async def _api_call(self, methods: MethodChain[Any, Any]) -> JMAPResponse:
        urns = set(
            self.session.type_registry[
                method.method_name.split("/")[0]
            ]
            for method in methods.calls
        )

        async with self.session.client as session:
            body = {
                    "using":[*urns],
                    "methodCalls": [
                        [*call[:3]]
                        for call in methods.calls
                    ]
                }

            resp = await session.post(
                self.session.api_url,
                headers={"Content-Type": "application/json"},
                json = body
            )
            content = await resp.content.read()
            return JMAPResponse.model_validate_json(content)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None]:  # pyright: ignore[reportIncompatibleMethodOverride]
        for i in range(self.settings.max_concurrent_requests):
            await self._add_worker(i)
        yield

        for signal in self._workers_stops:
            signal.set()

        _ = await asyncio.gather(*self._workers)

    async def _core_worker(self, stop_signal: asyncio.Event) -> None:
        wait_to_end = asyncio.create_task(stop_signal.wait())
        keep_waiting = True

        while keep_waiting:
            wait_for_task = asyncio.create_task(self._backlog.get())
            done, pending = await asyncio.wait(
                (
                    wait_for_task,
                    wait_to_end
                ),
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                result = task.result()
                if result is True:
                    keep_waiting = False
                    continue

                values, future = result
                try:
                    future.set_result(
                        await self._api_call(values)
                    )
                except Exception as e:
                    future.set_exception(e)

            if not keep_waiting:
                for task in pending:
                    _ = task.cancel()
                    with suppress(asyncio.CancelledError):
                        __ = await task
                return
