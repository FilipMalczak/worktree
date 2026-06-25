from pathlib import Path
from typing import Protocol, Iterable, runtime_checkable, Literal, assert_never


class Named(Protocol):
    def name(self) -> str: ...

@runtime_checkable
class Localizable(Named, Protocol):
    def name(self) -> str:
        return self.path().name

    def path(self) -> Path:
        """
        This is the path of self, not its parent - it should include the self.name() segment at the end
        """

ObjectType = Literal["text", "binary"]

@runtime_checkable
class Object[RawSequence](Localizable, Protocol):
    """
    A generic abstraction of a file. RawSequence is what this maps to in-memory (bytes, str, but maybe there are
    more interesting use cases).
    """

    def object_type(self) -> ObjectType: ...

    def read(self) -> RawSequence: ...
    def write(self, data: RawSequence): ...

    @classmethod
    def subclass_for_type(cls, object_type: ObjectType) -> type[Object]:
        match object_type:
            case "text": return TextObject
            case "binary": return BinaryObject
            case _ as never: assert_never(never)


@runtime_checkable
class BinaryObject(Object[bytes], Protocol):
    def object_type(self) -> ObjectType:
        return "binary"

    def read(self) -> bytes: ...
    def write(self, data: bytes): ...


@runtime_checkable
class TextObject(Object[str], Protocol):
    def object_type(self) -> ObjectType:
        return "text"

    def read(self) -> str: ...
    def write(self, data: str): ...


#fixme rethink name
class WrongAccessibleTypeException(Exception):
    """
    Raised by AgnosticCollection.find(p, t) when AgnosticCollection.exists(p) is True, but the underlying structure does
    not comply to t (we are looking for a collection, but there's an object there, or vice versa; no exception on binary
    object found when looking for text one or the other way around).
    """


@runtime_checkable
#fixme poor name choice
class AgnosticCollection(Named, Protocol):
    def ls(self) -> Iterable[Accessible]: ...

    def rm(self, path: str | Path):
        """
        Must accept path to any accessible (both objects and collections); in filesystem terms, must allow to delete
        a single file or a whole directory (even if it has children).
        """

    #fixme filesystem abstraction leaks here; "mkcollection"?
    def mkdir(self, path: str | Path) -> Collection:
        """
        Must work in way parallel to makedirs(exists_ok=True), no matter where mounted
        """

    def touch[T: Object](self, path: str | Path, t: type[T] | ObjectType) -> T: ...

    def find[T: Accessible](self, path: str | Path, t: type[T] | ObjectType) -> T | None:
        """
        :raise WrongAccessibleTypeException:
        LOOK OUT! Exception raised on object/collection mismatch! No issues if looking for text object and finding binary
        or vice versa!
        """

    def exists(self, path: str | Path) -> bool: ...


@runtime_checkable
class Collection(AgnosticCollection, Localizable, Protocol):
    """
    A generic abstraction of a directory. Should operate on Objects and Collections, not their names;
    """
    pass # this is agnostic collection with path; no specific behavior here otherwise


Accessible = Object | Collection

RootCollection = AgnosticCollection

#fixme class name, param name, arg name - all suck; rethink
class AccessibilityProtocol[Details](Protocol):
    def attach(self, mountpoint: Details) -> RootCollection: ...