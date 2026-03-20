import asyncio
import os

from dotenv import load_dotenv

from jmapy.auth import BasicLogin
from jmapy.session import start_session

if not load_dotenv():
    raise FileNotFoundError

cred = BasicLogin(
    os.environ["EMAIL"],
    os.environ["PASSWORD"]
)

async def main() -> None:
    await start_session(
        cred,
        nameservers=["1.1.1.1"]
    )

if __name__ == "__main__":
    asyncio.run(main())
