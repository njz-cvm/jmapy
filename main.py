import asyncio
import json
from typing import Self

from aiohttp import ClientSession
from dotenv import dotenv_values

from jmapy.auth import BasicLogin
from jmapy.orm.base import DataType, Reference
from jmapy.orm.get import GettableData
from jmapy.orm.query import QueryableData
from jmapy.session import start_session
from jmapy.transport import unpack

env = dotenv_values()

cred = BasicLogin(
    env["EMAIL"],  # pyright: ignore[reportArgumentType]
    env["PASSWORD"]  # pyright: ignore[reportArgumentType]
)

class Mailbox(
    QueryableData,
    GettableData,
    DataType
):
    name: Reference[Self, str] = Reference[Self, str]()

def make_request[T](using: list[str], data: T) -> dict[str, list[str] | T]:
    return {
        "using": using,
        "methodCalls": data
    }

async def main() -> None:
    resp = await start_session(
        cred,
        nameservers=["1.1.1.1"]
    )

    inbox_fetch = make_request(
        ["urn:ietf:params:jmap:mail"],
        unpack(
            Mailbox.query(
                resp.primary_accounts["urn:ietf:params:jmap:mail"],
                # filter=Mailbox.name == "Outbox"
            ).then(
                lambda q: \
                Mailbox.get(
                    resp.primary_accounts["urn:ietf:params:jmap:mail"],
                    q.ids
                )
            )
        )
    )

    print(json.dumps(inbox_fetch, indent=2))

    async with ClientSession(middlewares=[cred.middleware]) as sess:
        data = await sess.post(
            resp.api_url,
            json = inbox_fetch
        )
        print(json.dumps(await data.json(), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
