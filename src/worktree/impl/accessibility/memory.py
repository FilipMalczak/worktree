from pathlib import Path
from typing import Iterable, Any, Dict

from worktree.mounting.accessible import (
    MountDriver,
    Collection,
    Object,
    Accessible,
    WrongAccessibleTypeException,
    RootCollection,
    NoMountpoint,
    AccessibleType,
)


class InMemoryStorage:
    def __init__(self):
        # A simple nested directory structure representation
        # Directory node: {"type": "directory", "children": {name: node}}
        # File node: {"type": "file", "content": bytes}
        self.root = {"type": "directory", "children": {}}

    def _resolve_parts(self, path: Path) -> list[str]:
        # Normalize relative path components
        parts = []
        for part in path.parts:
            if part in ("/", "\\", ".", ""):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return parts

    def get_node(self, path: Path) -> Dict[str, Any] | None:
        parts = self._resolve_parts(path)
        current = self.root
        for part in parts:
            if current["type"] != "directory" or part not in current["children"]:
                return None
            current = current["children"][part]
        return current

    def mkdir(self, path: Path):
        parts = self._resolve_parts(path)
        current = self.root
        for part in parts:
            if part not in current["children"]:
                current["children"][part] = {"type": "directory", "children": {}}
            current = current["children"][part]
            if current["type"] != "directory":
                raise WrongAccessibleTypeException(f"Path segment '{part}' is a file, cannot create directory.")

    def touch(self, path: Path) -> Dict[str, Any]:
        parts = self._resolve_parts(path)
        if not parts:
            raise WrongAccessibleTypeException("Cannot touch root path.")
        
        # Ensure parent directory exists
        parent_parts = parts[:-1]
        current = self.root
        for part in parent_parts:
            if part not in current["children"]:
                current["children"][part] = {"type": "directory", "children": {}}
            current = current["children"][part]
            if current["type"] != "directory":
                raise WrongAccessibleTypeException(f"Path segment '{part}' is a file, cannot create parent directory.")
        
        filename = parts[-1]
        if filename in current["children"]:
            node = current["children"][filename]
            if node["type"] == "directory":
                raise WrongAccessibleTypeException(f"Path '{path}' is a directory, cannot touch as file.")
        else:
            current["children"][filename] = {"type": "file", "content": b""}
            node = current["children"][filename]
        return node

    def delete(self, path: Path):
        parts = self._resolve_parts(path)
        if not parts:
            # Cannot delete root
            return
        
        parent_parts = parts[:-1]
        current = self.root
        for part in parent_parts:
            if current["type"] != "directory" or part not in current["children"]:
                return
            current = current["children"][part]
            
        filename = parts[-1]
        if filename in current["children"]:
            del current["children"][filename]


class InMemoryCollection(Collection):
    def __init__(self, storage: InMemoryStorage, path: Path):
        self._storage = storage
        self._path = path

    def path(self) -> Path:
        return self._path

    def name(self) -> str:
        # For root path, name is empty, but let's handle it gracefully
        return self._path.name or ""

    def _resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to(p.anchor)
        resolved = (self._path / p).resolve()
        # InMemory path resolution should be relative to workspace or mock root
        # We can just return resolved path normalized
        return resolved

    def ls(self) -> Iterable[Accessible]:
        node = self._storage.get_node(self._path)
        if not node or node["type"] != "directory":
            return
        for name, child_node in node["children"].items():
            child_path = self._path / name
            if child_node["type"] == "directory":
                yield InMemoryCollection(self._storage, child_path)
            else:
                yield InMemoryObject(self._storage, child_path)

    def rm(self, path: str | Path):
        p = self._resolve_path(path)
        self._storage.delete(p)

    def mkdir(self, path: str | Path) -> Collection:
        p = self._resolve_path(path)
        self._storage.mkdir(p)
        return InMemoryCollection(self._storage, p)

    def touch(self, path: str | Path) -> Object:
        p = self._resolve_path(path)
        self._storage.touch(p)
        return InMemoryObject(self._storage, p)

    def find(self, path: str | Path, accessible_type: AccessibleType = "any") -> Accessible | None:
        p = self._resolve_path(path)
        node = self._storage.get_node(p)
        if node is None:
            return None

        if node["type"] == "directory":
            if accessible_type == "object":
                raise WrongAccessibleTypeException(f"Expected object at '{p}', but found collection.")
            return InMemoryCollection(self._storage, p)
        else:
            if accessible_type == "collection":
                raise WrongAccessibleTypeException(f"Expected collection at '{p}', but found object.")
            return InMemoryObject(self._storage, p)

    def exists(self, path: str | Path, accessible_type: AccessibleType = "any") -> bool:
        p = self._resolve_path(path)
        node = self._storage.get_node(p)
        if node is None:
            return False
        if accessible_type == "any":
            return True
        elif accessible_type == "object":
            return node["type"] != "directory"
        elif accessible_type == "collection":
            return node["type"] == "directory"
        return False


class InMemoryObject(Object):
    def __init__(self, storage: InMemoryStorage, path: Path):
        self._storage = storage
        self._path = path

    def path(self) -> Path:
        return self._path

    def _get_node(self):
        node = self._storage.get_node(self._path)
        if not node or node["type"] == "directory":
            raise FileNotFoundError(f"No in-memory file at {self._path}")
        return node

    def read_text(self) -> str:
        return self._get_node()["content"].decode("utf-8")

    def write_text(self, data: str):
        node = self._storage.touch(self._path)
        node["content"] = data.encode("utf-8")

    def read_binary(self) -> bytes:
        return self._get_node()["content"]

    def write_binary(self, data: bytes):
        node = self._storage.touch(self._path)
        node["content"] = data


class InMemoryMountDriver(MountDriver[NoMountpoint]):
    def mount(self, mountpoint: NoMountpoint) -> RootCollection:
        return InMemoryCollection(InMemoryStorage(), Path("/"))