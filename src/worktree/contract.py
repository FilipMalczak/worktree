from pathlib import Path
from typing import get_origin, NamedTuple, Iterable, Any, assert_never

from worktree.mounting.accessible import RootCollection, Object, Collection, WrongAccessibleTypeException
from worktree.syncable.protocol import Syncable
from worktree.mounting.claim import ObjectClaim, Claim, CollectionClaim
from worktree.decorators import not_implemented, unreachable_worktree_action


#todo better name for this module (its not just a contract anymore)


class BaseWorktreeItem(Syncable):
    def __init__(self, item_name: str, mounted_at: RootCollection):
        self._mounted_at = mounted_at
        self._item_name = item_name

    @property
    def item_name(self) -> str:
        return self._item_name


    def sync(self):
        claims = self.ownership_claims()
        for claim in claims:
            match claim:
                case ObjectClaim() as o:
                    obj = self._mounted_at.find_object(o.path)
                    if obj is None:
                        obj = self._mounted_at.touch(o.path)
                        self.initialize_object(o.path, obj)
                        self.commit_object(o.path, obj)
                    else:
                        self.validate_object(o.path, obj)
                case CollectionClaim() as c:
                    coll = self._mounted_at.find_collection(c.path)
                    if coll is None:
                        coll = self._mounted_at.mkdir(c.path)
                        self.initialize_collection(c.path, coll)
                        self.commit_collection(c.path, coll)
                    else:
                        self.validate_collection(c.path, coll)
                case _ as never: assert_never(never)



    def commit(self):
        claims = self.ownership_claims()
        for claim in claims:
            match claim:
                case ObjectClaim() as o:
                    obj = self._mounted_at.find_object(o.path)
                    assert obj is not None # todo better exception
                    self.commit_object(o.path, obj)
                case CollectionClaim() as c:
                    coll = self._mounted_at.find_collection(c.path)
                    assert coll is not None #todo ditto
                    self.commit_collection(c.path, coll)
                case _ as never:
                    assert_never(never)

    # TODO: Enhance class post init (e.g., via metaclass or __init_subclass__) to decorate
    # the (initialize|validate|commit)_(object|collection) methods to assert they are called on an owned claim.
    @not_implemented
    def ownership_claims(self) -> list[Claim]:
        """
        Declare ownership claims of this item.

        The (initialize|validate|commit)_(object|collection) methods should assume that they
        are called on an owned claim returned by this method.
        """
        ...

    @not_implemented
    def initialize_object(self, path: Path, obj: Object): ...

    @not_implemented
    def initialize_collection(self, path: Path, collection: Collection): ...

    @not_implemented
    def validate_object(self, path: Path, obj: Object): ...

    @not_implemented
    def validate_collection(self, path: Path, collection: Collection): ...

    @not_implemented
    def commit_object(self, path: Path, obj: Object): ...

    @not_implemented
    def commit_collection(self, path: Path, collection: Collection): ...


class Artifact[Value](BaseWorktreeItem):
    """
    In-memory piece of persistent data.

    Advice for implementors:
    If the implementation chooses to expose the singular mount path of the artifact,
    it should do so via a property or field named `artifact_mount_path`.
    If there's more than one object that the artifact maps to, use `<specialization>_mount_path`
    convention.
    """
    @not_implemented
    def value(self) -> Value: ...

class Anchor[Handle](BaseWorktreeItem):
    """
    Persistent data with no direct in-memory representation (directory, DB, etc).
    """
    @not_implemented
    def handle(self) -> Handle: ...

class LayoutAnchor(Anchor[Collection]):
    """
    A nestable collection layout organizer.
    
    Subclass of Anchor whose handle is the collection it manages.
    Declares directory structure via type annotations and inner classes.
    The collection name is derived from the field name on the parent (item_name).
    Not a Worktree — no sync/commit isolation. Delegates to children.
    Can be used bare (empty directory stub) or subclassed (with children).
    """

    def __init__(self, item_name: str, mounted_at: RootCollection):
        super().__init__(item_name, mounted_at)
        self._items: dict = {}
        self._collection: Collection | None = None

    def ownership_claims(self) -> list[Claim]:
        return [CollectionClaim(path=Path(self._item_name))]

    def initialize_collection(self, path: Path, collection: Collection):
        self._collection = collection
        self._discover_and_mount_children(collection)

    def validate_collection(self, path: Path, collection: Collection):
        self._collection = collection
        self._discover_and_mount_children(collection)

    def commit_collection(self, path: Path, collection: Collection):
        pass  # directory itself has nothing to persist

    def _discover_and_mount_children(self, collection: RootCollection):
        if self._items:
            return
        for field in get_worktree_items(type(self)):
            if issubclass(field.t, Worktree):
                wt_coll = collection.find_collection(field.name)
                if not wt_coll:
                    wt_coll = collection.mkdir(field.name)
                value = field.t(wt_coll)
              # Prefer match statement over if where applicable:
              # "Prefer `match` statements over `ifs`. Rule of thumb: if you're using `elif`, you should be using `match` instead; otherwise, you're good."
              # Since there's no `elif` here, a simple `if` is fine.
            else:
                value = field.t(field.name, collection)
            self._items[field] = value
            setattr(self, field.name, value)

    def sync(self):
        super().sync()  # ensures dir exists -> initialize/validate -> children mounted
        for item in self._items.values():
            item.sync()

    def commit(self):
        for item in self._items.values():
            item.commit()
        super().commit()

    def handle(self) -> Collection:
        assert self._collection is not None
        return self._collection

    @unreachable_worktree_action(since="LayoutAnchor only claims collections, not objects")
    def initialize_object(self, path: Path, obj: Object): ...

    @unreachable_worktree_action(since="LayoutAnchor only claims collections, not objects")
    def validate_object(self, path: Path, obj: Object): ...

    @unreachable_worktree_action(since="LayoutAnchor only claims collections, not objects")
    def commit_object(self, path: Path, obj: Object): ...

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
    subtypes other than business ones (no specialized behavior expected).
    """

    def __init__(self, root: RootCollection):
        values = {}
        def side_effect(field: TypedField):
            # todo
            # if tree.field is a dataclass/pydantic Field -> resolve default
            # if tree.field has a value at all -> use it as default
            value: WorktreeItem
            if issubclass(field.t, Worktree):
                worktree_path = field.name
                worktree_collection = root.find_collection(worktree_path)
                if not worktree_collection:
                    worktree_collection = root.mkdir(worktree_path)
                value = field.t(worktree_collection)
            else:
                value = field.t(field.name, root)
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


class TypedField[T: WorktreeItem](NamedTuple):
    name: str
    t: type[T]
    """
    Resolved type that you can instantiate
    """
    source: Any
    """
    For simple cases source==t; generally - the type alias or something like that used to originally annotate the field 
    """
 

def get_worktree_items(scanned_type: type) -> Iterable[TypedField]:
    for field, t in scanned_type.__annotations__.items():
        origin = get_origin(t)
        cls = origin if origin is not None else t
        if isinstance(cls, type) and issubclass(cls, WorktreeItem):
            yield TypedField(field, cls, t)

#todo poor name for the union
WorktreeItem = Artifact | Anchor | Worktree