import asyncio
import os

from dotenv import load_dotenv

from jmapy import start_session
from jmapy.auth import BasicLogin
from jmapy.capability.core import Core


async def main() -> None:
    auth = BasicLogin(
        os.environ["EMAIL"],
        os.environ["PASSWORD"]
    )
    async with await start_session(auth) as session:
        resp = await session.execute(
            Core.echo({
                "abc": 123
            }).tag("echoed")
        )

        print(
            resp.get(dict[str, int], "echoed")
        )

if __name__ == "__main__":
    assert load_dotenv()
    asyncio.run(main())
