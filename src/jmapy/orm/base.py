from collections.abc import Callable
from typing import Any, NamedTuple, Self, overload

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
    resp_cls: type[Any]


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
            class BoundResponse(last_call.resp_cls):
                __call_id__ = last_call.call_id
                __method_name__ = last_call.method_name
                __path_prefix__ = ""

            next_chain = cmd(BoundResponse) # type: ignore
            return MethodChain(self.calls + next_chain.calls)
        else:
            return MethodChain(self.calls + cmd.calls)
