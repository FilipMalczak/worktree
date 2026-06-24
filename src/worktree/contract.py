from typing import Self, get_origin, NamedTuple, Iterable, Any

from src.worktree.mounting.accessible import RootCollection
from src.worktree.syncable.base import BaseSyncable
from src.worktree.syncable.protocol import Syncable


class Artifact[Value=Self](BaseSyncable):
    """
    In-memory piece of persistent data.
    """
    def value(self) -> Value: ...

class Anchor[Handle](BaseSyncable):
    """
    Persistent data with no direct in-memory representation (directory, DB, etc).
    """
    def handle(self) -> Handle: ...

class Worktree(Syncable):
    """
    Root object used to declare the shape of the syncable tree. Can be mounted inside other worktrees and syncables
    (where applicable).

    It is not an Anchor nor an Artifact.
    It represents a composable, but standalone unit, while Artifacts and Anchors are used to fill it in.
    Composability is guided by code reuse, not by synchronization. If you mount W1 that has W2 as an item, and then
    mount W2 separately, commits from W2 won't change in-memory state of W1 and vice versa.
    THIS MIGHT LEAD TO STATE LOSS! But that's a design choice. Use this library accordingly or suffer the consequences.

    This is part of the contract, but also provides the default behavior. It is not expected for this class to have
    subtypes other than business ones (no specialized behavor expected).
    """

    def __init__(self, root: RootCollection):
        values = {}
        def side_effect(field: TypedField):
            # todo
            # if tree.field is a dataclass/pydantic Field -> resolve default
            # if tree.field has a value at all -> use it as default
            if issubclass(field.t, Worktree):
                value = field.t(root)
            else:
                value = field.t()
            values[field] = value
            setattr(self, field.name, value)
        for field in get_worktree_items(type(self)):
            side_effect(field)
        self._items = values

    def sync(self):
        for item in self._items.values():
            item.sync()

    def commit(self):
        # fixme this is not really atomic
        for item in self._items.values():
            item.commit()


class TypedField(NamedTuple):
    name: str
    t: type
    """
    Resolved type that you can instantiate
    """
    source: Any
    """
    For simple cases source==t; generally - the type alias or something like that used to originally represent the field 
    """

def get_worktree_items(scanned_type: type) -> Iterable[WorktreeItem]:
    for field, t in scanned_type.__annotations__.items():
        origin = get_origin(t)
        cls = origin if origin is not None else t
        if isinstance(scanned_type, type) and issubclass(cls, WorktreeItem):
            yield TypedField(field, cls, t)

#todo poor name for the union
WorktreeItem = Artifact | Anchor | Worktree