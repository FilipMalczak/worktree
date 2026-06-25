import os
import shutil
from pathlib import Path
from typing import Iterable

from worktree.mounting.accessible import (
    MountDriver,
    Collection,
    Object,
    Accessible,
    WrongAccessibleTypeException,
    RootCollection,
)


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
                yield FilesystemObject(child)

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

    def touch(self, path: str | Path) -> Object:
        p = self._resolve_path(path)
        if p.exists():
            if p.is_dir():
                raise WrongAccessibleTypeException(f"Path '{p}' is a directory, cannot touch as file.")
            p.touch()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        return FilesystemObject(p)

    def find(self, path: str | Path) -> Accessible | None:
        p = self._resolve_path(path)
        if not p.exists():
            return None

        if p.is_dir():
            return FilesystemCollection(p)
        else:
            return FilesystemObject(p)

    def exists(self, path: str | Path) -> bool:
        return self._resolve_path(path).exists()


class FilesystemObject(Object):
    def __init__(self, path: Path):
        self._path = path

    def path(self) -> Path:
        return self._path

    def read_text(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def write_text(self, data: str):
        self._path.write_text(data, encoding="utf-8")

    def read_binary(self) -> bytes:
        return self._path.read_bytes()

    def write_binary(self, data: bytes):
        self._path.write_bytes(data)


class FilesystemMountDriver(MountDriver[Path | str]):
    def mount(self, mountpoint: Path | str) -> RootCollection:
        return FilesystemCollection(Path(mountpoint).resolve())