import json
import pytest

from worktree.contract import Worktree, LayoutAnchor
from worktree.mounting.base import BaseMounter
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint

from test_layout_anchor import ChildArtifact, NestedLayout, ParentLayout, Artifact1, Artifact2, ThisThing


class BareWorktree(Worktree):
    bare: LayoutAnchor


class NestedWorktree(Worktree):
    layout: NestedLayout


class ParentWorktree(Worktree):
    parent: ParentLayout


class ThisThingWorktree(Worktree):
    this_thing: ThisThing


def test_bare_layout_anchor_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    assert not root.exists("bare")
    tree = mounter.mount(BareWorktree)
    assert root.exists("bare")
    assert root.find_collection("bare") is not None


def test_subclassed_layout_with_artifact_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    assert not root.exists("layout")
    tree = mounter.mount(NestedWorktree)
    assert root.exists("layout")
    assert root.exists("layout/child.json")
    
    assert isinstance(tree.layout.child, ChildArtifact)
    assert tree.layout.child.value_field == "default_val"


def test_nested_layout_anchors_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    tree = mounter.mount(ParentWorktree)
    
    assert root.exists("parent")
    assert root.exists("parent/nested")
    assert root.exists("parent/nested/child.json")
    assert root.exists("parent/direct_child.json")
    
    assert tree.parent.direct_child.value_field == "default_val"
    assert tree.parent.nested.child.value_field == "default_val"


def test_layout_anchor_sync_loads_existing_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Pre-populate files
    parent_dir = root.mkdir("parent")
    nested_dir = parent_dir.mkdir("nested")
    nested_dir.touch("child.json").write_text('{"value_field": "existing_nested"}')
    parent_dir.touch("direct_child.json").write_text('{"value_field": "existing_direct"}')
    
    mounter = BaseMounter(root)
    tree = mounter.mount(ParentWorktree)
    
    assert tree.parent.direct_child.value_field == "existing_direct"
    assert tree.parent.nested.child.value_field == "existing_nested"


def test_layout_anchor_commit_persists_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    tree = mounter.mount(ParentWorktree)
    
    tree.parent.direct_child.value_field = "updated_direct"
    tree.parent.nested.child.value_field = "updated_nested"
    
    tree.commit()
    
    # Verify file contents
    direct_data = json.loads(root.find("parent/direct_child.json").read_text())
    assert direct_data == {"value_field": "updated_direct"}
    
    nested_data = json.loads(root.find("parent/nested/child.json").read_text())
    assert nested_data == {"value_field": "updated_nested"}


def test_layout_anchor_handle_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    tree = mounter.mount(NestedWorktree)
    
    handle = tree.layout.handle()
    assert handle is not None
    assert handle.name() == "layout"


# test_layout_anchor_unreachable_object_methods cannot be duplicated in the E2E suite
# because object lifecycle methods are only called internal to the WorktreeItem sync
# and are not reachable/applicable via the public Worktree/Mounter interface.


def test_worktree_with_nested_layouts_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    tree = mounter.mount(ThisThingWorktree)
    
    assert root.exists("this_thing")
    assert root.exists("this_thing/artifact1.json")
    assert root.exists("this_thing/baz")
    assert root.exists("this_thing/baz/x")
    assert root.exists("this_thing/baz/y")
    assert root.exists("this_thing/baz/y/a")
    assert root.exists("this_thing/baz/y/b")
    assert root.exists("this_thing/foobar")
    assert root.exists("this_thing/foobar/artifact2.json")
    
    assert tree.this_thing.artifact1.val == "v1"
    assert tree.this_thing.foobar.artifact2.val == "v2"
    assert isinstance(tree.this_thing.baz.x, LayoutAnchor)
    assert isinstance(tree.this_thing.baz.y.a, LayoutAnchor)

