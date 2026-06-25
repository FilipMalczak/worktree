from pathlib import Path
from typing import Iterable, Literal, assert_never

from worktree.decorators import not_implemented


class Named:
    @not_implemented
    def name(self) -> str: ...


class Localizable(Named):
    def name(self) -> str:
        return self.path().name

    @not_implemented
    def path(self) -> Path:
        """
        This is the path of self, not its parent - it should include the self.name() segment at the end
        """

ObjectType = Literal["text", "binary"]


class Object[RawSequence](Localizable):
    """
    A generic abstraction of a file. RawSequence is what this maps to in-memory (bytes, str, but maybe there are
    more interesting use cases).
    """

    @not_implemented
    def object_type(self) -> ObjectType: ...

    @not_implemented
    def read(self) -> RawSequence: ...

    @not_implemented
    def write(self, data: RawSequence): ...

    @classmethod
    def subclass_for_type(cls, object_type: ObjectType) -> type[Object]:
        match object_type:
            case "text": return TextObject
            case "binary": return BinaryObject
            case _ as never: assert_never(never)


class BinaryObject(Object[bytes]):
    def object_type(self) -> ObjectType:
        return "binary"

    @not_implemented
    def read(self) -> bytes: ...

    @not_implemented
    def write(self, data: bytes): ...


class TextObject(Object[str]):
    def object_type(self) -> ObjectType:
        return "text"

    @not_implemented
    def read(self) -> str: ...

    @not_implemented
    def write(self, data: str): ...


#fixme rethink name
class WrongAccessibleTypeException(Exception):
    """
    Raised by AgnosticCollection.find(p, t) when AgnosticCollection.exists(p) is True, but the underlying structure does
    not comply to t (we are looking for a collection, but there's an object there, or vice versa; no exception on binary
    object found when looking for text one or the other way around).
    """


#fixme poor name choice
class AgnosticCollection(Named):
    @not_implemented
    def ls(self) -> Iterable[Accessible]: ...

    @not_implemented
    def rm(self, path: str | Path):
        """
        Must accept path to any accessible (both objects and collections); in filesystem terms, must allow to delete
        a single file or a whole directory (even if it has children).
        """

    #fixme filesystem abstraction leaks here; "mkcollection"?
    @not_implemented
    def mkdir(self, path: str | Path) -> Collection:
        """
        Must work in way parallel to makedirs(exists_ok=True), no matter where mounted
        """

    @not_implemented
    def touch[T: Object](self, path: str | Path, t: type[T] | ObjectType) -> T: ...

    @not_implemented
    def find[T: Accessible](self, path: str | Path, t: type[T] | ObjectType) -> T | None:
        """
        :raise WrongAccessibleTypeException:
        LOOK OUT! Exception raised on object/collection mismatch! No issues if looking for text object and finding binary
        or vice versa!
        """

    @not_implemented
    def exists(self, path: str | Path) -> bool: ...


class Collection(AgnosticCollection, Localizable):
    """
    A generic abstraction of a directory. Should operate on Objects and Collections, not their names;
    """
    pass # this is agnostic collection with path; no specific behavior here otherwise


Accessible = Object | Collection

RootCollection = AgnosticCollection

#fixme class name, param name, arg name - all suck; rethink
class AccessibilityProtocol[Details]:
    @not_implemented
    def attach(self, mountpoint: Details) -> RootCollection: ...