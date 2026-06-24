from pathlib import Path
from typing import Protocol, Iterable, runtime_checkable


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


@runtime_checkable
class Object[RawSequence](Localizable, Protocol):
    """
    A generic abstraction of a file. RawSequence is what this maps to in-memory (bytes, str, but maybe there are
    more interesting use cases).
    """

    def read(self) -> RawSequence: ...
    def write(self, data: RawSequence): ...


@runtime_checkable
class BinaryObject(Object[bytes], Protocol):
    def read(self) -> bytes: ...
    def write(self, data: bytes): ...


@runtime_checkable
class TextObject(Object[str], Protocol):
    def read(self) -> str: ...
    def write(self, data: str): ...


@runtime_checkable
#fixme poor name choice
class AgnosticCollection(Named, Protocol):
    def ls(self) -> Iterable[Accessible]: ...
    def rm(self, path: str | Path): ...
    def mkdir(self, path: str | Path):
        """
        Must work in way parallel to makedirs(exists_ok=True), no matter where mounted
        """
    def touch[T: Object](self, path: str | Path, t: type[T]) -> T: ...


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