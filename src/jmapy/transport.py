
import datetime
import json
from typing import Any, Self

from jmapy.models import ID
from jmapy.orm.base import DataType, MethodChain, Reference
from jmapy.orm.filtering import or_
from jmapy.orm.get import GettableData
from jmapy.orm.query import QueryableData

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
print(foo)

if __name__ == "__main__":
    exec(
    User.get("12", ["223"]).then(
        lambda usr: Foo.get(usr.account_id, ["123"]).then(
        lambda foo: Bar.get(foo.account_id, foo.list.all.attr).then(
        Foo.query("123", or_(Foo.attr == "123", Foo.attr == "321"), [Foo.bar])
        )))
    )
