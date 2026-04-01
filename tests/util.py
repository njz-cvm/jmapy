from typing import Any

from jmapy.orm.base import DEFAULT_ACCOUNT, MethodChain


def dump_exec[T, *Ts](test: MethodChain[T, *Ts]) -> list[tuple[str, dict[str, Any], str]]:
    requests: list[tuple[str, dict[str, Any], str]] = [call[:-2] for call in test.calls]
    solved_requests: list[tuple[str, dict[str, Any], str]] = []
    for name, data, call in requests:
        for key, value in data.items():
            if isinstance(value, DEFAULT_ACCOUNT):
                data[key] = "x"
        solved_requests.append((name, data, call))
    return solved_requests
