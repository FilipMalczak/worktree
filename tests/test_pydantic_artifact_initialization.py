import json
import pytest
from pydantic import Field
from worktree.contract import MissingInitialStateError
from worktree.impl.items.pydantic_model import PydanticArtifact
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint


class SampleConfig(PydanticArtifact):
    username: str = "default_user"
    port: int = 8080


class RequiredConfig(PydanticArtifact):
    db_url: str
    username: str = "db_user"


def test_direct_initialization():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Initialize directly with initial_states
    config = SampleConfig(
        "config", 
        root, 
        initial_states={"username": "alice", "port": 1234}
    )
    
    assert config.username == "alice"
    assert config.port == 1234
    
    assert not root.exists("config.json")
    config.sync()
    assert root.exists("config.json")
    
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "alice", "port": 1234}


def test_partial_initialization():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Initialize with partial initial_states override
    config = SampleConfig(
        "config", 
        root, 
        initial_states={"username": "bob"}
    )
    
    assert config.username == "bob"
    assert config.port == 8080  # fallback to default
    
    config.sync()
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "bob", "port": 8080}


def test_no_arg_compatibility():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Initialize with no initial_states
    config = SampleConfig("config", root)
    
    assert config.username == "default_user"
    assert config.port == 8080
    
    config.sync()
    data = json.loads(root.find("config.json").read_text())
    assert data == {"username": "default_user", "port": 8080}


def test_required_fields_with_initial_states():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    
    # Providing required fields succeeds
    config = RequiredConfig(
        "db",
        root,
        initial_states={"db_url": "postgresql://localhost/db"}
    )
    assert config.db_url == "postgresql://localhost/db"
    assert config.username == "db_user"
    
    # Omitting required fields raises MissingInitialStateError
    with pytest.raises(MissingInitialStateError) as exc_info:
        RequiredConfig("db", root)
        
    assert "Missing required fields: db_url" in str(exc_info.value)
    assert exc_info.value.item_name == "db_url"
    assert exc_info.value.__cause__ is not None  # raised from Pydantic ValidationError
