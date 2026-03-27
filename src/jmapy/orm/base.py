from collections.abc import Callable, Iterable, Mapping
from typing import (
    Any,
    NamedTuple,
    Protocol,
    Self,
    dataclass_transform,
    overload,
    override,
    runtime_checkable,
)

from jmapy.models import ID
from jmapy.orm.filtering import FilterCondition, FilterOperator


def _to_camel(snake_str: str) -> str:
    """Converts snake_case attributes to JMAP camelCase JSON keys."""
    words = snake_str.split('_')
    return words[0] + ''.join(w.title() for w in words[1:])


@runtime_checkable
class Serializable(Protocol):

    def to_dict(self) -> dict[str, Any]: ...


def bind_arg(key: str, value: Any, *, keep_none: bool = False) -> dict[str, Any]:
    if value is None and not keep_none:
        return {}

    if isinstance(value, Mapping):
        return {
            key:
            {
                (item_key.to_dict() if isinstance(item_key, Serializable) else item_key): \
                (item_value.to_dict() if isinstance(item_value, Serializable) else item_value)
                for item_key, item_value in value.items()  # pyright: ignore[reportUnknownVariableType]
            }
        }

    if isinstance(value, Iterable) and not isinstance(value, str):
        return {
            key: 
            [
                (item.to_dict() if isinstance(item, Serializable) else item)
                for item in value  # pyright: ignore[reportUnknownVariableType]
            ]
        }

    if isinstance(value, Serializable) and getattr(value, "result_of", None):
        return {f"#{key}": value.to_dict()}
    elif isinstance(value, Serializable):
        return {key: value.to_dict()}
    else:
        return {key: value}


def json_ptr_escape(part: str) -> str:
    return (
        part
        .replace("~", "~0")
        .replace("/", "~1")
    )

class Reference[T, P]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        self.nullable: bool = True
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name

    def __hash__(self) -> int:
        return hash(self.path)

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = "/" + json_ptr_escape(
            _to_camel(name)
        )

    @override
    def __eq__(self, value: P, /) -> FilterCondition:  # pyright: ignore[reportIncompatibleMethodOverride]
        return FilterCondition(
            self.attr_name,
            value
        )
    
    @override
    def __ne__(self, value: P, /) -> FilterOperator:  # pyright: ignore[reportIncompatibleMethodOverride]
        return FilterOperator(
            "NOT",
            [FilterCondition(
                self.attr_name,
                value
            )]
        )

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
        
        value = obj.__dict__.get(self.attr_name)
        if value is None and not self.nullable:
            raise ValueError("Value not founded, but attribute is not nullable.")
        return value  # pyright: ignore[reportReturnType]

    def __set__(self, obj: T, value: P) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        """Serializes to an RFC 8620 Result Reference."""
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}

class NullReference[T, P](Reference[T, P]):

    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "") -> None:
        super().__init__(
            result_of=result_of,
            method_name=method_name,
            path=path,
            attr_name=attr_name
        )
        self.nullable = True

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> Self: ...
    @overload
    def __get__(self, obj: T, objtype: type[T] | None = None) -> P | None: ...
    def __get__(self, obj: T | None, objtype: type[T] | None = None) -> Self | P | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().__get__(obj, objtype)  # pyright: ignore[reportCallIssue, reportUnknownVariableType, reportArgumentType]


class BoundListReferenceAll:
    """Helper to catch wildcard attribute accesses like `foo.list.all.attr`"""
    def __init__(self, result_of: str, method_name: str, path: str):
        self.result_of = result_of
        self.method_name = method_name
        self.path = path

    def __hash__(self) -> int:
        return hash(self.path)
        
    def __getattr__(self, name: str) -> Reference[Any, Any]:
        return Reference(
            result_of=self.result_of,
            method_name=self.method_name,
            path=f"{self.path}/" + json_ptr_escape(
                _to_camel(name)
            ),
            attr_name=name
        )


class ListReference[T, P]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name
        self.nullable = False

    def __hash__(self) -> int:
        return hash(self.path)

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = "/" + json_ptr_escape(
            _to_camel(name)
        )

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

        value = obj.__dict__.get(self.attr_name, [])

        if value is None and not self.nullable:
            raise ValueError("Value not founded, but attribute is not nullable.")
        return value

    def __getitem__(self, key: int) -> type[P]:
        return BoundListReferenceAll(self.result_of, self.method_name, f"{self.path}/{key}") # type: ignore

    def __set__(self, obj: T, value: list[P]) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}


class NullListReference[T, P](ListReference[T, P]):

    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        super().__init__(
            result_of=result_of,
            method_name=method_name,
            path=path,
            attr_name=attr_name
        )
        self.nullable = True

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> Self: ...
    @overload
    def __get__(self, obj: T, objtype: type[T] | None = None) -> list[P] | None: ...
    def __get__(self, obj: T | None, objtype: type[T] | None = None) -> Self | list[P] | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().__get__(obj, objtype)  # pyright: ignore[reportCallIssue, reportUnknownVariableType, reportArgumentType]


class DictReference[T, K, V]:
    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name
        self.nullable = False

    def __hash__(self) -> int:
        return hash(self.path)

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = "/" + json_ptr_escape(
            _to_camel(name)
        )

    @overload
    def __get__(self, obj: None, objtype: Any) -> Self: ...

    @overload
    def __get__(self, obj: T, objtype: Any = None) -> dict[K, V]: ...

    def __get__(self, obj: T | None, objtype: Any = None) -> Self | dict[K, V]:
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


class NullDictReference[T, K, P](DictReference[T, K, P]):

    def __init__(self, result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        super().__init__(
            result_of=result_of,
            method_name=method_name,
            path=path,
            attr_name=attr_name
        )
        self.nullable = True

    @overload
    def __get__(self, obj: None, objtype: type[T]) -> Self: ...
    @overload
    def __get__(self, obj: T, objtype: type[T] | None = None) -> dict[K, P] | None: ...
    def __get__(self, obj: T | None, objtype: type[T] | None = None) -> Self | dict[K, P] | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        return super().__get__(obj, objtype)  # pyright: ignore[reportCallIssue, reportUnknownVariableType, reportArgumentType]


class DataTypeMeta(type):
    __refs__: list[Reference[type, Any] | ListReference[type, Any] | DictReference[type, Any, Any]]

    def __new__(
        cls: type[type],
        name: str,
        bases: tuple[type, ...],
        dct: dict[str, Any],
        **kwargs: Any
    ) -> type:
        dct["__refs__"] = [
            val
            for val in dct.values()
            if isinstance(val, (Reference, ListReference, DictReference))
        ]
        new_cls = super().__new__(cls, name, bases, dct, **kwargs)  # pyright: ignore[reportCallIssue, reportUnknownVariableType]
        return new_cls  # pyright: ignore[reportUnknownVariableType]

class _DataType(metaclass=DataTypeMeta):
    
    def __init__(self, **kwargs: Any) -> None:
        for ref in self.__class__.__refs__:
            if ref.attr_name in kwargs:
                self.__dict__[ref.attr_name] = kwargs[ref.attr_name]  # pyright: ignore[reportIndexIssue]
            elif ref.nullable:
                setattr(self, ref.attr_name, None)
            # else:
            #     msg = f"{self.__class__.__name__} missing keyword arguement: '{ref.attr_name}'"
            #     raise TypeError(msg)

@dataclass_transform(field_specifiers=(Reference, ListReference, NullReference, DictReference))
class DataType(_DataType): ...


class MethodCall(NamedTuple):
    method_name: str
    args: dict[str, Any]
    call_id: str
    resp_cls: type[Any]


class MethodChain[S, *Ts]:
    _calls: tuple[S, *Ts]

    def __init__(self, calls: list[MethodCall]):
        self.calls = calls

    @overload
    def resolve(self, target: type[int]) -> int | str: ...

    @overload
    def resolve(self, target: type[str]) -> str | list[str]: ...

    @overload
    def resolve[T](self, target: type[T]) -> T: ...

    def resolve[T](self, target: type[T]) -> T | None | int | str | list[str]: ...

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
