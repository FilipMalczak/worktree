import functools
from typing import Any, Callable

def not_implemented(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for bodyless/abstract methods.
    Raises NotImplementedError when called.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        class_name = ""
        if args:
            inst = args[0]
            if isinstance(inst, type):
                class_name = f" of class {inst.__name__}"
            else:
                class_name = f" of {inst.__class__.__name__} instance"
        raise NotImplementedError(f"Method '{func.__name__}'{class_name} is not implemented")
    return wrapper
