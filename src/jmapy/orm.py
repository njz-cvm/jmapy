
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple, Protocol, Self, overload

from jmapy.models import ID


def _to_camel(snake_str: str) -> str:
    """Converts snake_case attributes to JMAP camelCase JSON keys."""
    words = snake_str.split('_')
    return words[0] + ''.join(w.title() for w in words[1:])


class Property[T, P]:

    @overload
    def __get__(self, obj: type[T]) -> Self: ...

    @overload
    def __get__(self, obj: T, objtype: type[T]) -> P: ...

    def __get__(self, obj: T | type[T], objtype: type[T] | None = None) -> Self | P: ...


class Reference[T, P]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "") -> None:
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = f"/{_to_camel(name)}"

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> Self: ...
    @overload
    def __get__(self, obj: T, objtype: type[T] | None = None) -> P: ...
    def __get__(self, obj: T | None, objtype: type[T] | None = None) -> Self | P:
        if obj is None:
            # When called inside .then() lambda, objtype will hold JMAP metadata
            call_id = getattr(objtype, '__call_id__', None)
            if not call_id:
                return self
            
            # Return a bound version of the reference with the accumulated JSON path
            method_name = getattr(objtype, '__method_name__', "")
            path_prefix = getattr(objtype, '__path_prefix__', "")
            return self.__class__(
                result_of=call_id,
                method_name=method_name,
                path=f"{path_prefix}{self.path}",
                attr_name=self.attr_name
            )
        return obj.__dict__.get(self.attr_name)  # pyright: ignore[reportReturnType]

    def __set__(self, obj: T, value: P) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        """Serializes to an RFC 8620 Result Reference."""
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}


class BoundListReferenceAll:
    """Helper to catch wildcard attribute accesses like `foo.list.all.attr`"""
    def __init__(self, result_of: str, method_name: str, path: str):
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        
    def __getattr__(self, name: str) -> Reference[Any, Any]:
        return Reference(
            result_of=self.result_of,
            method_name=self.method_name,
            path=f"{self.path}/{_to_camel(name)}",
            attr_name=name
        )


class ListReference[T, P]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "") -> None:
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = f"/{_to_camel(name)}"

    @property
    def all(self) -> type[P]: 
        # Type hint satisfies static analysis; runtime intercepts paths
        return BoundListReferenceAll(self.result_of, self.method_name, f"{self.path}/*") # type: ignore

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> Self: ...
    @overload
    def __get__(self, obj: T, objtype: type[T] | None = None) -> list[P]: ...
    def __get__(self, obj: T | None, objtype: type[T] | None = None) -> Self | list[P]:
        if obj is None:
            call_id = getattr(objtype, '__call_id__', None)
            if not call_id:
                return self
            method_name = getattr(objtype, '__method_name__', "")
            path_prefix = getattr(objtype, '__path_prefix__', "")
            
            return self.__class__(
                result_of=call_id,
                method_name=method_name,
                path=f"{path_prefix}{self.path}",
                attr_name=self.attr_name
            )
        return obj.__dict__.get(self.attr_name, [])

    def __set__(self, obj: T, value: list[P]) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}


class DictReference[T, V]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "") -> None:
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = f"/{_to_camel(name)}"

    @overload
    def __get__(self, obj: None, objtype: Any) -> Self: ...

    @overload
    def __get__(self, obj: T, objtype: Any = None) -> dict[ID, V]: ...

    def __get__(self, obj: T | None, objtype: Any = None) -> Self | dict[ID, V]:
        if obj is None:
            call_id = getattr(objtype, '__call_id__', None)
            if not call_id:
                return self
            method_name = getattr(objtype, '__method_name__', "")
            path_prefix = getattr(objtype, '__path_prefix__', "")
            
            return self.__class__(
                result_of=call_id,
                method_name=method_name,
                path=f"{path_prefix}{self.path}",
                attr_name=self.attr_name
            )
        return obj.__dict__.get(self.attr_name, {})

    def __set__(self, obj: T, value: dict[ID, V]) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}


class MethodCall(NamedTuple):
    method_name: str
    args: dict[str, Any]
    call_id: str


class MethodChain[S, *Ts]:
    def __init__(self, calls: list[MethodCall]):
        self.calls = calls

    @overload
    def then[T, *Rs](self, cmd: "Callable[[type[S]], MethodChain[T, *Rs]]") -> "MethodChain[S, T, *Rs, *Ts]": ...
    @overload
    def then[T, *Rs](self, cmd: "MethodChain[T, *Rs]") -> "MethodChain[S, T, *Rs]": ...
    def then[T, *Rs](self, cmd: "Callable[[type[S]], MethodChain[T, *Rs]] | MethodChain[T, *Rs]") -> "MethodChain[S, T, *Rs, *Ts] | MethodChain[S, T, *Rs]":
        if callable(cmd):
            # Extract metadata from the immediately preceding call
            last_call = self.calls[-1]

            # Dynamically subclass to pass context to the descriptors
            class BoundResponse(GetResponse[T]):
                __call_id__ = last_call.call_id
                __method_name__ = last_call.method_name
                __path_prefix__ = ""

            next_chain = cmd(BoundResponse) # type: ignore
            return MethodChain(self.calls + next_chain.calls)
        else:
            return MethodChain(self.calls + cmd.calls)

class GetResponse[T]:
    account_id = Reference[Self, str]()
    state = Reference[Self, str]()
    list = ListReference[Self, T]()
    not_found = ListReference[Self, ID]()

    # Explicit constructor mappings for actual responses

    if not TYPE_CHECKING:

        def __init__(
            self,
            account_id: str = "",
            state: str = "",
            list: "list[T] | None" = None,
            not_found: "list[ID] | None" = None
        ) -> None:
            self.account_id = account_id
            self.state = state
            self.list = list if list is not None else []
            self.not_found = not_found if not_found is not None else []


class GettableData(Protocol):
    @classmethod
    def get(
        cls,
        account_id: ID | Reference[Any, ID],
        ids: list[ID] | ListReference[Any, ID] | Reference[Any, ID],
        properties: list[str] | None | ListReference[Any, str] | Reference[Any, str] = None,
    ) -> MethodChain[GetResponse[Self]]:
        method_name = f"{cls.__name__}/get"
        args: dict[str, Any] = {}

        def bind_arg(key: str, value: Any):
            # Check if this parameter is a lazy JMAP Result Reference
            if hasattr(value, "to_dict") and getattr(value, "result_of", None):
                args[f"#{key}"] = value.to_dict()
            else:
                args[key] = value

        bind_arg("accountId", account_id)
        bind_arg("ids", ids)
        if properties is not None:
            bind_arg("properties", properties)

        # Generate a unique client-side call ID for this method
        call_id = f"c_{uuid.uuid4().hex[:6]}"
        return MethodChain([MethodCall(method_name, args, call_id)])


class ChangesResponse:
    account_id = Reference[Self, ID]()
    old_state = Reference[Self, str]()
    new_state = Reference[Self, str]()
    has_more_changes = Reference[Self, bool]()
    created = ListReference[Self, ID]()
    updated = ListReference[Self, ID]()
    destroyed = ListReference[Self, ID]()


class QueryResponse:
    account_id = Reference[Self, ID]()
    query_state = Reference[Self, str]()
    can_calculate_changes = Reference[Self, bool]()
    position = Reference[Self, int]()
    ids = ListReference[Self, ID]()
    total = Reference[Self, int]()
    limit = Reference[Self, int]()


class QueryChangesResponse[T]:
    account_id: Reference["QueryChangesResponse[T]", str] = Reference()
    old_query_state: Reference["QueryChangesResponse[T]", str] = Reference()
    new_query_state: Reference["QueryChangesResponse[T]", str] = Reference()
    total: Reference["QueryChangesResponse[T]", int] = Reference()
    removed: ListReference["QueryChangesResponse[T]", ID] = ListReference()
    # JMAP returns AddedItem objects (id, index) for queryChanges
    added: ListReference["QueryChangesResponse[T]", dict[str, Any]] = ListReference()

class SetResponse[T]:
    account_id: Reference["SetResponse[T]", str] = Reference()
    old_state: Reference["SetResponse[T]", str] = Reference()
    new_state: Reference["SetResponse[T]", str] = Reference()
    created: DictReference["SetResponse[T]", T] = DictReference()
    updated: DictReference["SetResponse[T]", T] = DictReference()
    destroyed: ListReference["SetResponse[T]", ID] = ListReference()
    not_created: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
    not_updated: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
    not_destroyed: DictReference["SetResponse[T]", dict[str, Any]] = DictReference()
