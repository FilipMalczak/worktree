# TODO: Extract the core test suite logic as a contract acceptance harness so that
# the same test suite can be run against any MountDriver implementation automatically.
# Currently, the test cases for both FilesystemMountDriver and InMemoryMountDriver
# are written to match and cover all core operations and edge cases.

import tempfile
from pathlib import Path
import pytest

from worktree.mounting.accessible import (
    WrongAccessibleTypeException,
    NoMountpoint,
    TextObject,
    BinaryObject,
    Collection,
)
from worktree.impl.accessibility.filesystem import FilesystemMountDriver
from worktree.impl.accessibility.memory import InMemoryMountDriver


def run_shared_driver_tests(root):
    # 1. Test exists on non-existent path
    assert not root.exists("foo")
    assert not root.exists("foo/bar")

    # 2. Test touch and read/write text file
    txt_file = root.touch("hello.txt", "text")
    assert isinstance(txt_file, TextObject)
    assert root.exists("hello.txt")
    assert txt_file.name() == "hello.txt"
    assert txt_file.path() == root.path() / "hello.txt"
    
    # Read initial empty content
    assert txt_file.read() == ""
    
    # Write and read
    txt_file.write("hello world")
    assert txt_file.read() == "hello world"

    # 3. Test touch and read/write binary file
    bin_file = root.touch("data.bin", "binary")
    assert isinstance(bin_file, BinaryObject)
    assert root.exists("data.bin")
    assert bin_file.read() == b""
    
    bin_file.write(b"\x00\x01\x02")
    assert bin_file.read() == b"\x00\x01\x02"

    # 4. Test mkdir
    sub_dir = root.mkdir("sub/folder")
    assert isinstance(sub_dir, Collection)
    assert root.exists("sub/folder")
    assert sub_dir.name() == "folder"

    # 5. Test touch inside sub_dir
    sub_file = sub_dir.touch("nested.txt", "text")
    assert sub_file.read() == ""
    sub_file.write("nested content")
    assert sub_file.read() == "nested content"
    assert root.exists("sub/folder/nested.txt")

    # 6. Test find
    # Find existing text file
    found_txt = root.find("hello.txt", "text")
    assert found_txt is not None
    assert found_txt.read() == "hello world"

    # Find existing collection
    found_coll = root.find("sub/folder", Collection)
    assert found_coll is not None
    assert found_coll.name() == "folder"

    # Find non-existent path
    assert root.find("non_existent", "text") is None

    # 7. Test find wrong type raises WrongAccessibleTypeException
    # Looking for a Collection but finding an Object
    with pytest.raises(WrongAccessibleTypeException):
        root.find("hello.txt", Collection)

    # Looking for an Object but finding a Collection
    with pytest.raises(WrongAccessibleTypeException):
        root.find("sub/folder", "text")

    # 8. Test touch on existing directory raises WrongAccessibleTypeException
    with pytest.raises(WrongAccessibleTypeException):
        root.touch("sub/folder", "text")

    # 9. Test ls
    items = list(root.ls())
    names = {item.name() for item in items}
    assert "hello.txt" in names
    assert "data.bin" in names
    assert "sub" in names

    # 10. Test rm
    # Remove file
    root.rm("data.bin")
    assert not root.exists("data.bin")

    # Remove directory recursively
    root.rm("sub")
    assert not root.exists("sub")
    assert not root.exists("sub/folder/nested.txt")


def test_filesystem_mount_driver():
    with tempfile.TemporaryDirectory() as tmpdir:
        driver = FilesystemMountDriver()
        root = driver.mount(tmpdir)
        run_shared_driver_tests(root)


def test_in_memory_mount_driver():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    run_shared_driver_tests(root)
