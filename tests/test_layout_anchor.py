import json
import pytest
from pathlib import Path

from worktree.contract import LayoutAnchor, WorktreeItem
from worktree.impl.items.pydantic_model import PydanticArtifact
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint
from worktree.decorators import UnreachableWorktreeAction


class ChildArtifact(PydanticArtifact):
    mount_path = "child.json"
    value_field: str = "default_val"


class NestedLayout(LayoutAnchor):
    child: ChildArtifact


class ParentLayout(LayoutAnchor):
    nested: NestedLayout
    direct_child: ChildArtifact


def test_bare_layout_anchor():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    bare = LayoutAnchor("bare_dir", root)
    assert not root.exists("bare_dir")
    
    bare.sync()
    assert root.exists("bare_dir")
    assert root.find_collection("bare_dir") is not None


def test_subclassed_layout_with_artifact():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    layout = NestedLayout("layout_dir", root)
    assert not root.exists("layout_dir")
    
    layout.sync()
    assert root.exists("layout_dir")
    assert root.exists("layout_dir/child.json")
    
    # Assert child is accessible as attribute
    assert isinstance(layout.child, ChildArtifact)
    assert layout.child.value_field == "default_val"


def test_nested_layout_anchors():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    parent = ParentLayout("parent_dir", root)
    parent.sync()
    
    assert root.exists("parent_dir")
    assert root.exists("parent_dir/nested")
    assert root.exists("parent_dir/nested/child.json")
    assert root.exists("parent_dir/child.json")
    
    assert parent.direct_child.value_field == "default_val"
    assert parent.nested.child.value_field == "default_val"


def test_layout_anchor_sync_loads_existing():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Pre-populate files
    parent_dir = root.mkdir("parent_dir")
    nested_dir = parent_dir.mkdir("nested")
    nested_dir.touch("child.json").write_text('{"value_field": "existing_nested"}')
    parent_dir.touch("child.json").write_text('{"value_field": "existing_direct"}')
    
    parent = ParentLayout("parent_dir", root)
    parent.sync()
    
    assert parent.direct_child.value_field == "existing_direct"
    assert parent.nested.child.value_field == "existing_nested"


def test_layout_anchor_commit_persists():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    parent = ParentLayout("parent_dir", root)
    parent.sync()
    
    parent.direct_child.value_field = "updated_direct"
    parent.nested.child.value_field = "updated_nested"
    
    parent.commit()
    
    # Verify file contents
    direct_data = json.loads(root.find("parent_dir/child.json").read_text())
    assert direct_data == {"value_field": "updated_direct"}
    
    nested_data = json.loads(root.find("parent_dir/nested/child.json").read_text())
    assert nested_data == {"value_field": "updated_nested"}


def test_layout_anchor_handle():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    layout = NestedLayout("layout_dir", root)
    layout.sync()
    
    handle = layout.handle()
    assert handle is not None
    assert handle.name() == "layout_dir"


def test_layout_anchor_unreachable_object_methods():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    layout = NestedLayout("layout_dir", root)
    
    with pytest.raises(UnreachableWorktreeAction):
        layout.initialize_object(Path("layout_dir"), root.touch("dummy"))
        
    with pytest.raises(UnreachableWorktreeAction):
        layout.validate_object(Path("layout_dir"), root.touch("dummy"))
        
    with pytest.raises(UnreachableWorktreeAction):
        layout.commit_object(Path("layout_dir"), root.touch("dummy"))

    assert "Unreachable method since LayoutAnchor only claims collections, not objects" in layout.initialize_object.__doc__
    assert ":raise UnreachableWorktreeAction:" in layout.initialize_object.__doc__
    assert "Unreachable method since LayoutAnchor only claims collections, not objects" in layout.validate_object.__doc__
    assert ":raise UnreachableWorktreeAction:" in layout.validate_object.__doc__
    assert "Unreachable method since LayoutAnchor only claims collections, not objects" in layout.commit_object.__doc__
    assert ":raise UnreachableWorktreeAction:" in layout.commit_object.__doc__


class Artifact1(PydanticArtifact):
    mount_path = "a1.json"
    val: str = "v1"


class Artifact2(PydanticArtifact):
    mount_path = "a2.json"
    val: str = "v2"


class ThisThing(LayoutAnchor):
    class Baz(LayoutAnchor):
        class Y(LayoutAnchor):
            a: LayoutAnchor
            b: LayoutAnchor
        x: LayoutAnchor
        y: Y
    class Foobar(LayoutAnchor):
        artifact2: Artifact2

    artifact1: Artifact1
    baz: Baz
    foobar: Foobar


def test_deep_nesting_with_mixed_children():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    this_thing = ThisThing("this_thing", root)
    this_thing.sync()
    
    assert root.exists("this_thing")
    assert root.exists("this_thing/a1.json")
    assert root.exists("this_thing/baz")
    assert root.exists("this_thing/baz/x")
    assert root.exists("this_thing/baz/y")
    assert root.exists("this_thing/baz/y/a")
    assert root.exists("this_thing/baz/y/b")
    assert root.exists("this_thing/foobar")
    assert root.exists("this_thing/foobar/a2.json")
    
    assert this_thing.artifact1.val == "v1"
    assert this_thing.foobar.artifact2.val == "v2"
    assert isinstance(this_thing.baz.x, LayoutAnchor)
    assert isinstance(this_thing.baz.y.a, LayoutAnchor)

