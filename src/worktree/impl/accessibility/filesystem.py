import os
import shutil
from pathlib import Path
from typing import Iterable

from worktree.mounting.accessible import (
    MountDriver,
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


def _is_binary_file(filepath: Path) -> bool:
    if not filepath.exists():
        return False
    try:
        with open(filepath, "tr", encoding="utf-8") as f:
            f.read(1024)
            return False
    except UnicodeDecodeError:
        return True
    except Exception:
        return False


class FilesystemCollection(Collection):
    def __init__(self, path: Path):
        self._path = path

    def path(self) -> Path:
        return self._path

    def name(self) -> str:
        return self._path.name

    def _resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            p = p.relative_to(p.anchor)
        resolved = (self._path / p).resolve()
        if not resolved.is_relative_to(self._path):
            return self._path
        return resolved

    def ls(self) -> Iterable[Accessible]:
        if not self._path.exists() or not self._path.is_dir():
            return
        for child in self._path.iterdir():
            if child.is_dir():
                yield FilesystemCollection(child)
            elif child.is_file():
                if _is_binary_file(child):
                    yield FilesystemBinaryObject(child)
                else:
                    yield FilesystemTextObject(child)

    def rm(self, path: str | Path):
        p = self._resolve_path(path)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()

    def mkdir(self, path: str | Path) -> Collection:
        p = self._resolve_path(path)
        p.mkdir(parents=True, exist_ok=True)
        return FilesystemCollection(p)

    def touch[T: Object](self, path: str | Path, t: type[T] | ObjectType) -> T:
        p = self._resolve_path(path)
        if isinstance(t, str):
            obj_type = t
        elif issubclass(t, BinaryObject):
            obj_type = "binary"
        else:
            obj_type = "text"

        if obj_type == "text":
            obj_cls = FilesystemTextObject
            default_content = ""
        else:
            obj_cls = FilesystemBinaryObject
            default_content = b""

        if p.exists():
            if p.is_dir():
                raise WrongAccessibleTypeException(f"Path '{p}' is a directory, cannot touch as file.")
            p.touch()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            if obj_type == "text":
                p.write_text(default_content, encoding="utf-8")
            else:
                p.write_bytes(default_content)
        return obj_cls(p)

    def find[T: Accessible](self, path: str | Path, t: type[T] | ObjectType) -> T | None:
        p = self._resolve_path(path)
        if not p.exists():
            return None

        is_collection = _is_collection_type(t)
        if is_collection:
            if not p.is_dir():
                raise WrongAccessibleTypeException(f"Expected directory at '{p}', but found a file.")
            return FilesystemCollection(p)
        else:
            if not p.is_file():
                raise WrongAccessibleTypeException(f"Expected file at '{p}', but found a directory.")
            if _is_binary_file(p):
                return FilesystemBinaryObject(p)
            else:
                return FilesystemTextObject(p)

    def exists(self, path: str | Path) -> bool:
        return self._resolve_path(path).exists()


class FilesystemTextObject(TextObject):
    def __init__(self, path: Path):
        self._path = path

    def path(self) -> Path:
        return self._path

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def write(self, data: str):
        self._path.write_text(data, encoding="utf-8")


class FilesystemBinaryObject(BinaryObject):
    def __init__(self, path: Path):
        self._path = path

    def path(self) -> Path:
        return self._path

    def read(self) -> bytes:
        return self._path.read_bytes()

    def write(self, data: bytes):
        self._path.write_bytes(data)


class FilesystemMountDriver(MountDriver[Path | str]):
    def mount(self, mountpoint: Path | str) -> RootCollection:
        return FilesystemCollection(Path(mountpoint).resolve())