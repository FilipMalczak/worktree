import json
import pytest
from pydantic import ValidationError

from worktree.contract import Worktree
from worktree.mounting.base import BaseMounter
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint
from test_pydantic_artifact import SampleConfig


class SampleWorktree(Worktree):
    config: SampleConfig


def test_pydantic_artifact_creation_and_initial_sync_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    assert not root.exists("config.json")
    
    # Mounting performs sync automatically
    tree = mounter.mount(SampleWorktree)
    assert root.exists("config.json")
    
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "default_user", "port": 8080}
    assert tree.config.username == "default_user"
    assert tree.config.port == 8080


def test_pydantic_artifact_sync_from_existing_object_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    root.touch("config.json").write_text('{"username": "admin", "port": 9000}')
    
    mounter = BaseMounter(root)
    # Mounting performs sync, which loads the existing object's fields
    tree = mounter.mount(SampleWorktree)
    assert tree.config.username == "admin"
    assert tree.config.port == 9000


def test_pydantic_artifact_commit_changes_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    tree = mounter.mount(SampleWorktree)
    
    tree.config.username = "new_user"
    tree.config.port = 443
    tree.commit()
    
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "new_user", "port": 443}


def test_pydantic_artifact_validation_error_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    root.touch("config.json").write_text('{"username": "admin", "port": "not-an-integer"}')
    
    mounter = BaseMounter(root)
    with pytest.raises(ValidationError):
        mounter.mount(SampleWorktree)


# test_pydantic_artifact_unreachable_collection_methods cannot be duplicated in the E2E suite
# because collection lifecycle methods are only called internal to the WorktreeItem sync
# and are not reachable/applicable via the public Worktree/Mounter interface.


