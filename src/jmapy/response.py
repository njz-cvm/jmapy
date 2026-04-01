
from typing import overload

from attr import dataclass

from jmapy.errors import (
    ChangesFailure,
    CopyFailure,
    GenericFailure,
    GetFailure,
    QueryChangesFailure,
    QueryFailure,
    SetFailure,
)
from jmapy.models import JMAPResponse
from jmapy.orm.base import MethodCall
from jmapy.orm.changes import ChangesResponse
from jmapy.orm.copy import CopyResponse
from jmapy.orm.get import GetResponse
from jmapy.orm.query import QueryResponse
from jmapy.orm.query_changes import QueryChangesResponse
from jmapy.orm.set import SetResponse


@dataclass(frozen=True, slots=True)
class Response[S, *Ts]:
    _responses: JMAPResponse
    _call: list[MethodCall]

    @overload
    def get[V](self, resp_cls: type[GetResponse[V]], tag: str | None = None, index: int | None = None) -> GetResponse[V] | GenericFailure | GetFailure: ...

    @overload
    def get(self, resp_cls: type[ChangesResponse], tag: str | None = None, index: int | None = None) -> ChangesResponse | GenericFailure | ChangesFailure: ...

    @overload
    def get[V](self, resp_cls: type[SetResponse[V]], tag: str | None = None, index: int | None = None) -> SetResponse[V] | GenericFailure | SetFailure: ...

    @overload
    def get[V](self, resp_cls: type[CopyResponse[V]], tag: str | None = None, index: int | None = None) -> CopyResponse[V] | GenericFailure | CopyFailure: ...

    @overload
    def get(self, resp_cls: type[QueryResponse], tag: str | None = None, index: int | None = None) -> QueryResponse | GenericFailure | QueryFailure: ...

    @overload
    def get[V](self, resp_cls: type[QueryChangesResponse[V]], tag: str | None = None, index: int | None = None) -> QueryChangesResponse[V] | GenericFailure | QueryChangesFailure: ...

    @overload
    def get[R](self, resp_cls: type[R], tag: str | None = None, index: int | None = None) -> R | GenericFailure: ...

    def get[R](self, resp_cls: type[R], tag: str | None = None, index: int | None = None) ->  R | GenericFailure \
        | GetFailure | ChangesFailure | SetFailure | CopyFailure | QueryFailure | QueryChangesFailure: ...

    def expect_all(self) -> tuple[S, *Ts]: ...

