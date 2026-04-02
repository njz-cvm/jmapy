
import asyncio
import datetime
from typing import Self

from pydantic import TypeAdapter

from jmapy.auth import BasicLogin
from jmapy.errors import GenericFailure, GetFailure
from jmapy.models import ID
from jmapy.orm.base import DataType, ListReference, MethodChain, Reference
from jmapy.orm.filtering import or_
from jmapy.orm.get import GetResponse, GettableData
from jmapy.orm.query import QueryableData
from jmapy.session import JMAPSession, start_session


class User(GettableData): ...

class Foo[T](GettableData, QueryableData, DataType):
    attr: Reference[Self, ID] = Reference[Self, ID](str)
    bar: Reference[Self, datetime.datetime] = Reference[Self, datetime.datetime](datetime.datetime)
    buzz: ListReference[Self, T] = ListReference[Self, T](T)

class Bar(GettableData, DataType):
    bar: Reference[Self, datetime.datetime] = Reference[Self, datetime.datetime](datetime.datetime)


def unpack[S, *Ts](chain: MethodChain[S, *Ts]) -> tuple[S, *Ts]:
    return tuple(
        c[:-1]
        for c in chain.calls
    )  # pyright: ignore[reportReturnType]

async def _main():
    ta = TypeAdapter[Foo[Bar]](Foo[Bar])
    res = ta.validate_python({
        "bar": "2026-04-02T15:06:52+0000",
        "buzz": [{"bar": "2026-04-02T15:06:52+0000"}, {"bar": "2026-04-02T15:06:52+0000"}]
    })

    chain = Foo[Bar].get(["123"])
    ta2 = TypeAdapter[GetResponse[Foo[Bar]]](chain.calls[0].resp_cls)
    res2 = (
        ta2.validate_python({
            "accountId": "awd",
            "state": "awd",
            "list": [{
                "bar": "2026-04-02T15:06:52+0000",
                "buzz": [{"bar": "2026-04-02T15:06:52+0000"}, {"bar": "2026-04-02T15:06:52+0000"}]
            }],
            "notFound": ["B123"]
        })
    )
    breakpoint()

    print(res)
    print(res.bar.hour)
    exit(0)

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