
import json
from typing import NewType, Self

from jmapy.models import ID
from jmapy.orm.base import DataType, MethodChain, Reference, _DataType
from jmapy.orm.get import GettableData

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

class Foo(GettableData, DataType):
    attr: Reference[Self, ID] = Reference[Self, ID]()

class Bar(GettableData): ...

foo = Foo(attr="id")
print(foo)

def exec[T, *Ts](test: MethodChain[T, *Ts]) -> None:
    print(
        json.dumps(
        [call[:-1] for call in test.calls], 
        indent=2)
    )


if __name__ == "__main__":
    exec(
    User.get("12", ["223"]).then(
        lambda usr: Foo.get(usr.account_id, ["123"]).then(
        lambda foo: Bar.get(foo.account_id, foo.list.all.attr).then(
        Foo.get("231", ["34"])
        )))
    )
