from typing import Any

from jmapy.orm.base import MethodChain


def dump_exec[T, *Ts](test: MethodChain[T, *Ts]) -> list[tuple[str, dict[str, Any], str]]:
    return [call[:-1] for call in test.calls]
