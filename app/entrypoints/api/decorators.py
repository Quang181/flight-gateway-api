from collections.abc import Callable
from typing import Any


def require_token(func: Callable[..., Any]) -> Callable[..., Any]:
    setattr(func, "_require_token", True)
    return func
