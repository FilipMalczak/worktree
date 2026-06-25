import os
from pathlib import Path
from typing import Iterable, Literal

from worktree.mounting.accessible import (
    MountDriver,
    NoMountpoint,
    Collection,
    Object,
    TextObject,
    BinaryObject,
    ObjectType,
    Accessible,
    WrongAccessibleTypeException,
    RootCollection,
)


def _is_collection_type(t: type | ObjectType) -> bool:
    if isinstance(t, str):
        return False
    return issubclass(t, Collection)


class InMemoryStorage:
    def __init__(self):
        self.nodes = {Path("."): {"type": "directory"}}

    def exists(self, path: Path) -> bool:
        return path in self.nodes

    def get_node(self, path: Path) -> dict | None:
        return self.nodes.get(path)

    def mkdir(self, path: Path):
        parts = path.parts
        for i in range(1, len(parts) + 1):
            ancestor = Path(*parts[:i])
            if ancestor not in self.nodes:
                self.nodes[ancestor] = {"type": "directory"}
            else:
                if self.nodes[ancestor]["type"] != "directory":
                    raise WrongAccessibleTypeException(
                        f"Expected directory at '{ancestor}', but found a file."
                    )

    def rm(self, path: Path):
        keys_to_remove = [
            k for k in self.nodes if k == path or path in k.parents
        ]
        for k in keys_to_remove:
            del self.nodes[k]

    def write_file(
        self, path: Path, content: str | bytes, file_type: Literal["text", "binary"]
    ):
        self.nodes[path] = {"type": file_type, "content": content}

    def read_file(self, path: Path) -> str | bytes:
        node = self.nodes.get(path)
        if node is None or node["type"] not in ("text", "binary"):
            raise FileNotFoundError(f"No file at '{path}'")
        return node["content"]


class InMemoryCollection(Collection):
    def __init__(self, storage: InMemoryStorage, path: Path):
        self._storage = storage
        self._path = path

    def path(self) -> Path:
        return self._path

    def name(self) -> str:
        return self._path.name

    def _resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to(p.anchor)
        resolved = Path(os.path.normpath(self._path / p))
        if resolved.parts and resolved.parts[0] == "..":
            return Path(".")
        return resolved

    def ls(self) -> Iterable[Accessible]:
        for k, node in self._storage.nodes.items():
            if k.parent == self._path and k != self._path:
                if node["type"] == "directory":
                    yield InMemoryCollection(self._storage, k)
                elif node["type"] == "text":
                    yield InMemoryTextObject(self._storage, k)
                elif node["type"] == "binary":
                    yield InMemoryBinaryObject(self._storage, k)

    def rm(self, path: str | Path):
        p = self._resolve_path(path)
        self._storage.rm(p)

    def mkdir(self, path: str | Path) -> Collection:
        p = self._resolve_path(path)
        self._storage.mkdir(p)
        return InMemoryCollection(self._storage, p)

    def touch[T: Object](self, path: str | Path, t: type[T] | ObjectType) -> T:
        p = self._resolve_path(path)
        if isinstance(t, str):
            obj_type = t
        elif issubclass(t, BinaryObject):
            obj_type = "binary"
        else:
            obj_type = "text"

        if obj_type == "text":
            obj_cls = InMemoryTextObject
            default_content = ""
        else:
            obj_cls = InMemoryBinaryObject
            default_content = b""

        if self._storage.exists(p):
            node = self._storage.get_node(p)
            if node["type"] == "directory":
                raise WrongAccessibleTypeException(
                    f"Path '{p}' is a directory, cannot touch as file."
                )
        else:
            self._storage.mkdir(p.parent)
            self._storage.write_file(p, default_content, obj_type)
        return obj_cls(self._storage, p)

    def find[T: Accessible](self, path: str | Path, t: type[T] | ObjectType) -> T | None:
        p = self._resolve_path(path)
        node = self._storage.get_node(p)
        if node is None:
            return None

        is_collection = _is_collection_type(t)
        if is_collection:
            if node["type"] != "directory":
                raise WrongAccessibleTypeException(
                    f"Expected directory at '{p}', but found a file."
                )
            return InMemoryCollection(self._storage, p)
        else:
            if node["type"] == "directory":
                raise WrongAccessibleTypeException(
                    f"Expected file at '{p}', but found a directory."
                )
            if node["type"] == "binary":
                return InMemoryBinaryObject(self._storage, p)
            else:
                return InMemoryTextObject(self._storage, p)

    def exists(self, path: str | Path) -> bool:
        return self._storage.exists(self._resolve_path(path))


class InMemoryTextObject(TextObject):
    def __init__(self, storage: InMemoryStorage, path: Path):
        self._storage = storage
        self._path = path

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        content = self._storage.read_file(self._path)
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return content

    def write(self, data: str):
        self._storage.write_file(self._path, data, "text")


class InMemoryBinaryObject(BinaryObject):
    def __init__(self, storage: InMemoryStorage, path: Path):
        self._storage = storage
        self._path = path

    def path(self) -> Path:
        return self._path

    def read(self) -> bytes:
        content = self._storage.read_file(self._path)
        if isinstance(content, str):
            return content.encode("utf-8")
        return content

    def write(self, data: bytes):
        self._storage.write_file(self._path, data, "binary")


class InMemoryMountDriver(MountDriver[NoMountpoint]):
    def mount(self, mountpoint: NoMountpoint) -> RootCollection:
        storage = InMemoryStorage()
        return InMemoryCollection(storage, Path("."))