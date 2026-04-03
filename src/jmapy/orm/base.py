import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Literal,
    NamedTuple,
    Protocol,
    Self,
    TypeVar,
    dataclass_transform,
    get_args,
    get_origin,
    overload,
    override,
    runtime_checkable,
)

from pydantic import BaseModel, Field, GetCoreSchemaHandler, create_model
from pydantic_core import core_schema

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

class DEFAULT_ACCOUNT: ...

type AnnotationLike[P] = type[P] | TypeVar | Annotated  # pyright: ignore[reportMissingTypeArgument]

class ReferenceBase[T, P]:
    path: str
    __ref_type__: AnnotationLike[P]

    def __init__(self, ref_type: AnnotationLike[P], result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        self.nullable: bool = False
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.attr_name = attr_name
        self.__ref_type__ = ref_type

    def __hash__(self) -> int:
        return hash(self.path)

    def __set_name__(self, owner: Any, name: str) -> None:
        self.attr_name = name
        self.path = "/" + json_ptr_escape(
            _to_camel(name)
        )

    def __set__(self, obj: T, value: P) -> None:
        obj.__dict__[self.attr_name] = value

    def to_dict(self) -> dict[str, str]:
        """Serializes to an RFC 8620 Result Reference."""
        return {"resultOf": self.result_of, "name": self.method_name, "path": self.path}


class Reference[T, P](ReferenceBase[T, P]):

    def __hash__(self) -> int:
        return hash(self.path)

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
                self.__ref_type__,
                result_of=call_id,
                method_name=method_name,
                path=f"{path_prefix}{self.path}",
                attr_name=self.attr_name
            )
        
        value = obj.__dict__.get(self.attr_name)
        if isinstance(value, DataTypeMeta.UNSET):
            raise ValueError("Accessing unset value. If this value was fetched, ensure this property was requested.")
        return value  # pyright: ignore[reportReturnType]


class NullReference[T, P](Reference[T, P]):

    def __init__(self, ref_type: AnnotationLike[P], result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "") -> None:
        super().__init__(
            ref_type,
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


class BoundListReferenceAll[P]:
    """Helper to catch wildcard attribute accesses like `foo.list.all.attr`"""
    def __init__(self, ref_type: AnnotationLike[P], result_of: str, method_name: str, path: str):
        self.result_of = result_of
        self.method_name = method_name
        self.path = path
        self.__ref_type__: AnnotationLike[P] = ref_type

    def __hash__(self) -> int:
        return hash(self.path)
        
    def __getattr__(self, name: str) -> Reference[Any, Any]:
        return Reference(
            self.__ref_type__,
            result_of=self.result_of,
            method_name=self.method_name,
            path=f"{self.path}/" + json_ptr_escape(
                _to_camel(name)
            ),
            attr_name=name
        )


class ListReference[T, P](ReferenceBase[T, P]):

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
                self.__ref_type__,
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


class NullListReference[T, P](ListReference[T, P]):

    def __init__(self, ref_type: AnnotationLike[P], result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        super().__init__(
            ref_type,
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


class DictReference[T, K, V](ReferenceBase[T, dict[K, V]]):
    __ref_type__: tuple[type[K], type[V] | TypeVar]  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, ref_key: AnnotationLike[K], ref_value: AnnotationLike[V], result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        super().__init__((ref_key, ref_value), result_of, method_name, path, attr_name, **kwargs)  # pyright: ignore[reportArgumentType]

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
                *self.__ref_type__,
                result_of=call_id,
                method_name=method_name,
                path=f"{path_prefix}{self.path}",
                attr_name=self.attr_name
            )
        return obj.__dict__.get(self.attr_name, {})


class NullDictReference[T, K, P](DictReference[T, K, P]):

    def __init__(self, ref_key: AnnotationLike[K], ref_value: AnnotationLike[P],  result_of: str = "", method_name: str = "", path: str = "", attr_name: str = "", **kwargs: Any) -> None:
        super().__init__(
            ref_key,
            ref_value,
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
    _parameterized_cache: dict[tuple[Any, ...], type]

    class UNSET: ...

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
        new_cls._parameterized_cache = {}
        return new_cls  # pyright: ignore[reportUnknownVariableType]

    if not TYPE_CHECKING:

        def __getitem__(cls, type_args: Any) -> type:
            """
            Intercepts generic subscription (e.g., GetResponse[AddedItem]).
            Generates a customized Pydantic model where TypeVars are explicitly replaced.
            """
            if not isinstance(type_args, tuple):
                type_args = (type_args,)

            if type_args in cls._parameterized_cache:
                return cls._parameterized_cache[type_args]

            name = f"{cls.__name__}[{','.join(getattr(t, '__name__', str(t)) for t in type_args)}]"  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
            new_cls = type.__new__(type(cls), name, (cls,), {"_is_parameterized": True})

            # 1. Extract the original TypeVars from the base class
            type_params: tuple[TypeVar, ...] = getattr(cls, "__type_params__", ())
            if not type_params and hasattr(cls, "__parameters__"):
                type_params = getattr(cls, "__parameters__")
                
            # 2. Create a mapping of TypeVar -> Resolved Type (e.g., {~T: AddedItem})
            type_mapping = dict(zip(type_params, type_args))  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]

            # 3. Rebuild the Pydantic model from scratch for this specific parameterization
            fields: dict[str, tuple[type, Any]] = {}
            for ref in cls.__refs__:
                
                # Map the TypeVars to the resolved types
                if isinstance(ref, DictReference):
                    key_type = type_mapping.get(ref.__ref_type__[0], ref.__ref_type__[0])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    val_type = type_mapping.get(ref.__ref_type__[1], ref.__ref_type__[1])  # pyright: ignore[reportUnknownMemberType, reportCallIssue, reportArgumentType, reportUnknownVariableType]
                    type_cls = dict[key_type, val_type]
                    
                elif isinstance(ref, ListReference):
                    base_type = type_mapping.get(ref.__ref_type__, ref.__ref_type__)  # pyright: ignore[reportUnknownMemberType, reportCallIssue, reportArgumentType, reportUnknownVariableType]
                    type_cls = list[base_type]
                    
                else:
                    type_cls = type_mapping.get(ref.__ref_type__, ref.__ref_type__)  # pyright: ignore[reportUnknownMemberType, reportCallIssue, reportArgumentType, reportUnknownVariableType]

                fields[ref.attr_name] = (
                    type_cls if not ref.nullable else (type_cls | None),
                    Field(
                        default=None if ref.nullable else cls.UNSET(),  # pyright: ignore[reportUnknownArgumentType]
                        alias=_to_camel(ref.attr_name)
                    )
                )

            # Generate a strictly typed, non-generic model for this specific instantiation
            new_cls.__pydantic_model__ = create_model(name, **fields)  # pyright: ignore
            
            cls._parameterized_cache[type_args] = new_cls
            return new_cls

class _DataType(metaclass=DataTypeMeta):
    __pydantic_model__: type[BaseModel]

    @classmethod
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Skip generation if this class was dynamically parameterized via __getitem__
        if not getattr(cls, "_is_parameterized", False):
            cls.__pydantic_init_subclass__(**kwargs)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        fields: dict[str, tuple[Any, Any]] = {}
        
        for ref in cls.__refs__:
            if isinstance(ref, DictReference):
                type_cls = dict[ref.__ref_type__[0], ref.__ref_type__[1]]
            elif isinstance(ref, ListReference):
                type_cls = list[ref.__ref_type__]
            else:
                type_cls = ref.__ref_type__

            fields[ref.attr_name] = (
                type_cls if not ref.nullable else (type_cls | None),
                Field(
                    default=None if ref.nullable else cls.UNSET(),
                    alias=_to_camel(ref.attr_name)
                )
            )

        cls.__pydantic_model__ = create_model(
            f"{cls.__name__}Model", 
            **fields  # pyright: ignore[reportArgumentType, reportCallIssue, reportUnknownVariableType]
        )

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Instructs Pydantic on how to handle recursive validation for _DataType fields.
        """
        # Determine if we are validating a generic alias
        origin = get_origin(source_type)
        if origin is not None and hasattr(origin, "__pydantic_model__"):
            args = get_args(source_type)
            pydantic_model = origin.__pydantic_model__[args]
        else:
            pydantic_model = cls.__pydantic_model__

        def validate_and_construct(value: Any) -> Any:
            if isinstance(value, cls):
                return value
            
            # Map raw dicts recursively into the resolved Pydantic model
            if isinstance(value, dict):
                validated_model = pydantic_model(**value)
            elif isinstance(value, pydantic_model):
                validated_model = value
            else:
                raise ValueError(f"Expected dict or {cls.__name__}, got {type(value)}")

            # Reconstruct the _DataType bypassing __init__ to prevent redundant re-validation
            obj = cls.__new__(cls)
            for ref in cls.__refs__:
                val = getattr(validated_model, ref.attr_name, cls.UNSET)
                obj.__dict__[ref.attr_name] = val  # pyright: ignore[reportIndexIssue]
            return obj

        return core_schema.no_info_plain_validator_function(validate_and_construct)
    
    def __init__(self, **kwargs: Any) -> None:
        for ref in self.__class__.__refs__:
            if ref.attr_name in kwargs:
                self.__dict__[ref.attr_name] = kwargs[ref.attr_name]  # pyright: ignore[reportIndexIssue]
            elif ref.nullable:
                setattr(self, ref.attr_name, None)

    def __repr__(self) -> str:
        all_props: list[str] = []
        for ref in self.__class__.__refs__:
            if isinstance(val := self.__dict__[ref.attr_name], DataTypeMeta.UNSET):
                all_props.append(f"{ref.attr_name}=<Not Provided>")
            else:
                all_props.append(f"{ref.attr_name}={repr(val)}")
        return f"{self.__class__.__name__}({', '.join(all_props)})"

    def raise_on_error(self) -> Self:
        return self

    def is_error(self) -> Literal[False]:
        return False

@dataclass_transform(field_specifiers=(Reference, ListReference, NullReference, DictReference))
class DataType(_DataType): ...


class MethodResponse:

    @classmethod
    def __new_call_id__(cls) -> str:
        return f"c_{uuid.uuid4().hex[:6]}"


class MethodCall(NamedTuple):
    method_name: str
    args: dict[str, Any]
    call_id: str
    resp_cls: type[Any]
    tag: str | None


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

    def tag(self, label: str) -> Self:
        last_call = self.calls[-1]._asdict()
        last_call["tag"] = label
        self.calls[-1] = MethodCall(**last_call)
        return self
