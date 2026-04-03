
from typing import overload

from attr import dataclass
from pydantic import TypeAdapter

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

JMAPY_VALIDATION_ERROR_MAP = {
    GetResponse: GetFailure,
    ChangesResponse: ChangesFailure,
    SetResponse: SetFailure,
    CopyResponse: CopyFailure,
    QueryResponse: QueryFailure,
    QueryChangesResponse: QueryChangesFailure
}


@dataclass(slots=True)
class Response[S, *Ts]:
    _responses: JMAPResponse
    _call: tuple[MethodCall, ...]

    @overload
    def get[V](self, resp_cls: type[GetResponse[V]], tag: str | None = None) -> GetResponse[V] | GenericFailure | GetFailure: ...

    @overload
    def get[V](self, resp_cls: type[GetResponse[V]], *, index: int | None = None) -> GetResponse[V] | GenericFailure | GetFailure: ...

    @overload
    def get(self, resp_cls: type[ChangesResponse], tag: str | None = None) -> ChangesResponse | GenericFailure | ChangesFailure: ...

    @overload
    def get(self, resp_cls: type[ChangesResponse], *, index: int | None = None) -> ChangesResponse | GenericFailure | ChangesFailure: ...

    @overload
    def get[V](self, resp_cls: type[SetResponse[V]], tag: str | None = None) -> SetResponse[V] | GenericFailure | SetFailure: ...

    @overload
    def get[V](self, resp_cls: type[SetResponse[V]], *, index: int | None = None) -> SetResponse[V] | GenericFailure | SetFailure: ...

    @overload
    def get[V](self, resp_cls: type[CopyResponse[V]], tag: str | None = None) -> CopyResponse[V] | GenericFailure | CopyFailure: ...

    @overload
    def get[V](self, resp_cls: type[CopyResponse[V]], *, index: int | None = None) -> CopyResponse[V] | GenericFailure | CopyFailure: ...

    @overload
    def get(self, resp_cls: type[QueryResponse], tag: str | None = None) -> QueryResponse | GenericFailure | QueryFailure: ...

    @overload
    def get(self, resp_cls: type[QueryResponse], *, index: int | None = None) -> QueryResponse | GenericFailure | QueryFailure: ...

    @overload
    def get[V](self, resp_cls: type[QueryChangesResponse[V]], tag: str | None = None) -> QueryChangesResponse[V] | GenericFailure | QueryChangesFailure: ...

    @overload
    def get[V](self, resp_cls: type[QueryChangesResponse[V]], *, index: int | None = None) -> QueryChangesResponse[V] | GenericFailure | QueryChangesFailure: ...

    @overload
    def get[R](self, resp_cls: type[R], tag: str | None = None) -> R | GenericFailure: ...

    @overload
    def get[R](self, resp_cls: type[R], *, index: int | None = None) -> R | GenericFailure: ...

    def get[R](self, resp_cls: type[R], tag: str | None = None, *, index: int | None = None) ->  R | GenericFailure \
        | GetFailure | ChangesFailure | SetFailure | CopyFailure | QueryFailure | QueryChangesFailure:

        if tag is not None and index is not None:
            msg = "Both 'tag' and 'index' were provided, but only one is allowed."
            raise TypeError(msg)

        if index is not None:
            if len(self._responses.method_responses) >= index:
                msg = f"No response found at index {index}. Total responses was {len(self._responses.method_responses)}."
                raise IndexError(msg)

            target_response = self._responses.method_responses[index]
        elif tag is not None:
            with_tag = next((call.call_id for call in self._call if call.tag == tag), None)

            if with_tag is None:
                msg = f"No call found using the tag '{tag}'."
                raise IndexError(msg)

            target_response = next(resp for resp in self._responses.method_responses if resp.call_id == with_tag)
        else:
            with_type = next((call.call_id for call in self._call if call.resp_cls is resp_cls), None)

            if with_type is None:
                msg = f"No call was expected to return with the response type '{resp_cls}'"
                raise IndexError(msg)

            target_response = next(resp for resp in self._responses.method_responses if resp.call_id == with_type)


        if resp_cls in JMAPY_VALIDATION_ERROR_MAP:
            validation_targets = resp_cls | GenericFailure | JMAPY_VALIDATION_ERROR_MAP[resp_cls]  # pyright: ignore[reportUnknownVariableType]
        else:
            validation_targets = resp_cls | GenericFailure

        adapter = TypeAdapter[validation_targets](validation_targets)  # pyright: ignore[reportUnknownVariableType]
        return adapter.validate_python(target_response.data)  # pyright: ignore[reportReturnType, reportUnknownVariableType]

    def expect_all(self) -> tuple[S, *Ts]:
        return tuple(
            TypeAdapter[call.resp_cls](call.resp_cls).validate_python(resp.data)
            for call, resp in zip(self._call, self._responses.method_responses)
        )
