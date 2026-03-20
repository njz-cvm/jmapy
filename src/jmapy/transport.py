
from collections.abc import Callable
from typing import Concatenate, Self, overload

session.request(
    Foo.changes(account_id, since_state).then(
        lambda resp: Foo.get(account_id, resp.created)
    )
)

session.request(
    Email.query(
        account_id,
        filter,
        sort,
        collapse_threads,
        position,
        limit,
        calculate_total
    ).then(
    lambda boxes: Email.get(account_id, boxes.ids).then(
    lambda emails: Thread.get(account_id, emails.list.all.thread_id).then(
    lambda threads: Email.get(account_id, threads.list.all.email_ids)
    )))
)

class Test[S, *Ts]:

    @overload
    def then[T, *Rs](self, cmd: "Callable[[S], Test[T, *Rs]]") -> "Test[S, T, *Rs, *Ts]": ...

    @overload
    def then[T, *Rs](self, cmd: "Test[T, *Rs]") -> "Test[S, T, *Rs]": ...

    def then[T, *Rs](self, cmd: "Callable[[S], Test[T, *Rs]] | Test[T, *Rs]") -> "Test[S, T, *Rs, *Ts] | Test[S, T, *Rs]": ...

class User:

    @classmethod
    def get(cls) -> Test[Self]: ...

class Foo:

    @classmethod
    def get(cls) -> Test[Self]: ...


class Bar:

    @classmethod
    def get(cls) -> Test[Self]: ...


def exec[T, *Ts](test: Test[T, *Ts]) -> tuple[T, *Ts]: ...

resp = exec(
    User.get().then(
        lambda usr: Foo.get().then(
        lambda foo: Bar.get().then(
        Foo.get()
        ))
    ),
) 
