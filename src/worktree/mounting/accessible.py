from pathlib import Path
from typing import Iterable

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


class Object(Localizable):
    """
    A unified abstraction of a file.
    """

    @not_implemented
    def read_text(self) -> str: ...

    @not_implemented
    def write_text(self, data: str): ...

    @not_implemented
    def read_binary(self) -> bytes: ...

    @not_implemented
    def write_binary(self, data: bytes): ...


#fixme rethink name
class WrongAccessibleTypeException(Exception):
    """
    Raised when we are looking for a collection but there's an object there, or vice versa.
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
    def touch(self, path: str | Path) -> Object: ...

    @not_implemented
    def find(self, path: str | Path) -> Accessible | None:
        """
        Finds the accessible resource (Object or Collection) at the given path.
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

class NoMountpoint:
    """
    If there are no details required to mount, use this token class.
    """

class MountDriver[Mountpoint]:
    @not_implemented
    def mount(self, mountpoint: Mountpoint) -> RootCollection: ...