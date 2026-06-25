import functools
from typing import Any, Callable

class UnreachableWorktreeAction(Exception):
    """
    Raised when an action is performed on an accessible type that this artifact does not claim.
    """
    pass


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


def unreachable_worktree_action(since: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for methods that are unreachable because the artifact does not claim that target type.
    Replaces the method body to raise UnreachableWorktreeAction and sets the docstring.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            raise UnreachableWorktreeAction(
                f"Method '{func.__name__}' is unreachable since {since}."
            )
        
        wrapper.__doc__ = (
            f"Unreachable method since {since}.\n\n"
            f":raise UnreachableWorktreeAction:"
        )
        return wrapper
    return decorator

