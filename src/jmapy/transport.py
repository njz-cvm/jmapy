
import asyncio
import datetime
from typing import Self

from jmapy.auth import BasicLogin
from jmapy.errors import GenericFailure, GetFailure
from jmapy.models import ID
from jmapy.orm.base import DataType, MethodChain, Reference
from jmapy.orm.filtering import or_
from jmapy.orm.get import GetResponse, GettableData
from jmapy.orm.query import QueryableData
from jmapy.session import JMAPSession, start_session

# session.request(
#     Foo.changes(account_id, since_state).then(
#         lambda resp: Foo.get(account_id, resp.created)
#     )
# )

# session.request(
#     Email.query(
#         account_id,
#         filter,
#         sort,
#         collapse_threads,
#         position,
#         limit,
#         calculate_total
#     ).then(
#     lambda boxes: Email.get(account_id, boxes.ids).then(
#     lambda emails: Thread.get(account_id, emails.list.all.thread_id).then(
#     lambda threads: Email.get(account_id, threads.list.all.email_ids)
#     )))
# )

class User(GettableData): ...

class Foo(GettableData, QueryableData, DataType):
    attr: Reference[Self, ID] = Reference[Self, ID]()
    bar: Reference[Self, datetime.datetime] = Reference[Self, datetime.datetime]()

class Bar(GettableData):
    bar: Reference[Self, datetime.datetime] = Reference[Self, datetime.datetime]()

foo = Foo(attr="id", bar=datetime.datetime.now())

def unpack[S, *Ts](chain: MethodChain[S, *Ts]) -> tuple[S, *Ts]:
    return tuple(
        c[:-1]
        for c in chain.calls
    )  # pyright: ignore[reportReturnType]

async def _main():
    session = JMAPSession(await start_session(BasicLogin("awd", "adw")))
    result = await session.execute(
        User.get(["223"]).then(
        lambda usr: Foo.get(["123"]).tag("foo-got").then(
        lambda foo: Bar.get(foo.list.all.attr).then(
        Foo.query(or_(Foo.attr == "123", Foo.attr == "321"), [Foo.bar])
        )))
    )
    values: GetResponse[Foo] | GenericFailure | GetFailure = result.get(GetResponse[Foo], "foo-got")
    result = values.raise_on_error()

if __name__ == "__main__":
    asyncio.run(_main())