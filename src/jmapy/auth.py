
from typing import Protocol

from aiohttp import BasicAuth, ClientHandlerType, ClientRequest, ClientResponse
from aiohttp.client_middlewares import ClientMiddlewareType
from attr import dataclass


class AccountAuthProtocol(Protocol):
    middleware: ClientMiddlewareType

    @property
    def domain(self) -> str | None: ...


@dataclass()
class BasicLogin(AccountAuthProtocol):
    email: str
    password: str

    async def middleware(self, request: ClientRequest, handler: ClientHandlerType) -> ClientResponse:  # pyright: ignore[reportIncompatibleMethodOverride]
        token = BasicAuth(
            self.email,
            self.password
        ).encode()
        request.headers["Authorization"] = token
        return await handler(request)

    @property
    def domain(self) -> str:
        return self.email.split("@")[-1]
