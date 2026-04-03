
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, Self

from aiodns import DNSResolver
from aiohttp import ClientSession
from pycares import SRVRecordData
from pydantic import BaseModel

from jmapy.auth import AccountAuthProtocol
from jmapy.capability.base import CapabilityType
from jmapy.capability.core import CoreCapability
from jmapy.errors import CapabilityNotSupported
from jmapy.models import SessionResponse
from jmapy.orm.base import MethodChain
from jmapy.response import Response

WELL_KNOWN_ENDPOINT = "/.well-known/jmap"


class JMAPSession:

    def __init__(self, session_values: SessionResponse, client: ClientSession, *capabilities: type[CapabilityType[Self, Any]]) -> None:
        self._values: SessionResponse = session_values
        self.client: ClientSession = client
        self._setting_cache: tuple[str, dict[str, BaseModel]]
        self.capabilities: dict[str, CapabilityType[Self, Any]] = {
            capability.URN: capability(self)
            for capability in capabilities
        }
        if CoreCapability.URN not in self.capabilities:
            self.capabilities[CoreCapability.URN] = CoreCapability(self)

        self.type_registry: dict[str, str]
        self._running: list[AbstractAsyncContextManager[None, bool | None]] = []

        for capability in self.capabilities.values():
            self.type_registry.update(
                dict.fromkeys((d.__name__ for d in capability.DATA_TYPES), capability.URN)
            )

    async def __aenter__(self) -> Self:
        if self._running:
            msg = "JMAP Session is already running, cannot start again."
            raise RuntimeError(msg)

        for capability in self.capabilities.values():
            self._running.append(capability.lifespan())
            await self._running[-1].__aenter__()

        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None):
        for lifetime in self._running:
            _ = await lifetime.__aexit__(exc_type, exc_val, exc_tb)
        self._running.clear()
        return False

    @property
    def core(self) -> CoreCapability[Self]:
        return self.capabilities[CoreCapability.URN]  # pyright: ignore[reportReturnType]

    @property
    def state(self) -> str:
        return self._values.state

    @property
    def api_url(self) -> str:
        return self._values.api_url

    def setting[T: BaseModel](self, urn: str, model: type[T]) -> T:
        if self._setting_cache[0] != self.state:
            self._setting_cache[1].clear()

        if urn not in self._setting_cache[1]:
            if urn not in self._values.capabilities:
                raise CapabilityNotSupported(urn)
            settings = model.model_validate(self._setting_cache[1][urn])
            self._setting_cache[1][urn] = settings

        return self._setting_cache[1][urn]  # pyright: ignore[reportReturnType]

    async def execute[S, *Ts](self, chain: "MethodChain[S, *Ts]") -> Response[S, *Ts]: ...  # pyright: ignore[reportGeneralTypeIssues]


async def _lookup_srv(
    hostname: str,
    service: str = "jmap",
    transport: str = "tcp",
    nameservers: Sequence[str] | None = None,
) -> list[SRVRecordData]:
    async with DNSResolver(nameservers) as resolver:
        print(f"_{service}._{transport}.{hostname}")
        results = await resolver.query_dns(
            f"_{service}._{transport}.{hostname}", "SRV"
        )
        return [
            record.data
            for record in results.answer
            if isinstance(record.data, SRVRecordData)
        ]

async def start_session(
    auth_provider: AccountAuthProtocol,
    *capabilities: str,
    jmap_session_endpoint: str | None = None,
    nameservers: Sequence[str] | None = None,
):
    if jmap_session_endpoint is not None:
        servers = [jmap_session_endpoint]
    elif auth_provider.domain is not None:
        servers = sorted(
            await _lookup_srv(auth_provider.domain, nameservers=nameservers),
            key=lambda s: s.priority
        )
        servers = [f"https://{s.target}:{s.port}" + WELL_KNOWN_ENDPOINT for s in servers]
    else:
        msg = "Unable determine JMAP session API location. Could not infer from auth provider, and endpoint not set manually using `jmap_session_endpoint`."
        raise ValueError(msg)

    async with ClientSession(middlewares=(auth_provider.middleware,)) as session:
        data = None

        for server in servers:
            resp = await session.get(server, allow_redirects=True)
            if resp.status != 200:
                print(await resp.json())
                breakpoint()
                continue
            data = await resp.content.read()
            
    if data is None:
        msg = "No JMAP Session APIs returned a successful response. Unable to configure session."
        raise ValueError(msg)

    session = SessionResponse.model_validate_json(data, strict=False)
    return session
