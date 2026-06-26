import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from worktree.impl.items.pydantic_model import PydanticArtifact
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint
from worktree.decorators import UnreachableWorktreeAction


class SampleConfig(PydanticArtifact):
    mount_path = "config.json"
    username: str = "default_user"
    port: int = 8080


def test_pydantic_artifact_creation_and_initial_sync():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    config = SampleConfig("config", root)
    
    assert not root.exists("config.json")
    config.sync()
    assert root.exists("config.json")
    
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "default_user", "port": 8080}


def test_pydantic_artifact_sync_from_existing_object():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    root.touch("config.json").write_text('{"username": "admin", "port": 9000}')
    
    config = SampleConfig("config", root)
    config.sync()
    assert config.username == "admin"
    assert config.port == 9000


def test_pydantic_artifact_commit_changes():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    config = SampleConfig("config", root)
    config.sync()
    
    config.username = "new_user"
    config.port = 443
    config.commit()
    
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "new_user", "port": 443}


def test_pydantic_artifact_validation_error():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    root.touch("config.json").write_text('{"username": "admin", "port": "not-an-integer"}')
    
    config = SampleConfig("config", root)
    with pytest.raises(ValidationError):
        config.sync()


def test_pydantic_artifact_unreachable_collection_methods():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    config = SampleConfig("config", root)
    
    with pytest.raises(UnreachableWorktreeAction):
        config.initialize_collection(Path("config.json"), root)
        
    with pytest.raises(UnreachableWorktreeAction):
        config.validate_collection(Path("config.json"), root)
        
    with pytest.raises(UnreachableWorktreeAction):
        config.commit_collection(Path("config.json"), root)

    # Verify docstring generation
    assert "Unreachable method since PydanticArtifact only claims objects, not collections" in config.initialize_collection.__doc__
    assert ":raise UnreachableWorktreeAction:" in config.initialize_collection.__doc__
    assert "Unreachable method since PydanticArtifact only claims objects, not collections" in config.validate_collection.__doc__
    assert ":raise UnreachableWorktreeAction:" in config.validate_collection.__doc__
    assert "Unreachable method since PydanticArtifact only claims objects, not collections" in config.commit_collection.__doc__
    assert ":raise UnreachableWorktreeAction:" in config.commit_collection.__doc__
