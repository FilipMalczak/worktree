import json
import pytest
from pathlib import Path
from pydantic import Field

from worktree.contract import Worktree, LayoutAnchor, BaseWorktreeItem, Anchor, MissingInitialStateError
from worktree.mounting.base import BaseMounter
from worktree.impl.accessibility.memory import InMemoryMountDriver
from worktree.mounting.accessible import NoMountpoint
from worktree.mounting.claim import ObjectClaim

from test_pydantic_artifact import SampleConfig
from worktree.impl.items.pydantic_model import PydanticArtifact


# Define the nested structure requested in the prompt
class SampleLayout(LayoutAnchor):
    config3: SampleConfig


class SampleWorktree(Worktree):
    config1: SampleConfig
    config2: SampleConfig
    layout: SampleLayout


# Define a required config with no defaults
class RequiredConfig(BaseWorktreeItem):
    # Let's make a Pydantic one first
    pass


class RequiredPydanticConfig(SampleConfig):
    required_key: str  # no default value


class RequiredWorktree(Worktree):
    config: RequiredPydanticConfig


class RequiredNestedConfig(PydanticArtifact):
    required_field: str


class RequiredNestedLayout(LayoutAnchor):
    config3: RequiredNestedConfig


class RequiredNestedWorktree(Worktree):
    layout: RequiredNestedLayout


# Define a non-Pydantic mock item that raises MissingInitialStateError when config is missing
class NonPydanticMockItem(Anchor[None]):
    def __init__(self, item_name: str, mounted_at, initial_states=None):
        super().__init__(item_name, mounted_at, initial_states=initial_states)
        if not initial_states or "required_val" not in initial_states:
            raise MissingInitialStateError(
                item_name="required_val",
                message="required_val is missing from initial_states"
            )
        self.val = initial_states["required_val"]

    def ownership_claims(self):
        return [ObjectClaim(path=Path(f"{self.item_name}.txt"))]

    def initialize_object(self, path, obj):
        obj.write_text(self.val)
        
    def validate_object(self, path, obj):
        self.val = obj.read_text()
        
    def commit_object(self, path, obj):
        obj.write_text(self.val)

    def handle(self) -> None:
        return None


class NonPydanticWorktree(Worktree):
    mock_item: NonPydanticMockItem


# Define a non-Pydantic mock item that raises a raw ValueError
class NonPydanticRawErrorMockItem(Anchor[None]):
    def __init__(self, item_name: str, mounted_at, initial_states=None):
        super().__init__(item_name, mounted_at, initial_states=initial_states)
        raise ValueError("raw initialization issue")

    def ownership_claims(self):
        return [ObjectClaim(path=Path(f"{self.item_name}.txt"))]

    def handle(self) -> None:
        return None


class NonPydanticRawErrorWorktree(Worktree):
    mock_item_raw: NonPydanticRawErrorMockItem


def test_nested_initialization_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    assert not root.exists("config1.json")
    assert not root.exists("config2.json")
    assert not root.exists("layout/config3.json")
    
    tree = mounter.mount(
        SampleWorktree,
        initial_states={
            "config1": {"username": "foo1", "port": 1},
            "config2": {"username": "foo2", "port": 2},
            "layout": {
                "config3": {"username": "foo3", "port": 3}
            }
        }
    )
    
    # Assert in-memory values are correct
    assert tree.config1.username == "foo1"
    assert tree.config1.port == 1
    assert tree.config2.username == "foo2"
    assert tree.config2.port == 2
    assert tree.layout.config3.username == "foo3"
    assert tree.layout.config3.port == 3
    
    # Assert files are persisted correctly
    assert root.exists("config1.json")
    assert root.exists("config2.json")
    assert root.exists("layout/config3.json")
    
    data1 = json.loads(root.find("config1.json").read_text())
    assert data1 == {"username": "foo1", "port": 1}
    
    data2 = json.loads(root.find("config2.json").read_text())
    assert data2 == {"username": "foo2", "port": 2}
    
    data3 = json.loads(root.find("layout/config3.json").read_text())
    assert data3 == {"username": "foo3", "port": 3}


def test_partial_initialization_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    # Override config1's username, config2's port, and leave layout.config3 untouched
    tree = mounter.mount(
        SampleWorktree,
        initial_states={
            "config1": {"username": "custom1"},
            "config2": {"port": 9999},
            "layout": {}
        }
    )
    
    assert tree.config1.username == "custom1"
    assert tree.config1.port == 8080  # fallback
    assert tree.config2.username == "default_user"  # fallback
    assert tree.config2.port == 9999
    assert tree.layout.config3.username == "default_user"  # fallback
    assert tree.layout.config3.port == 8080  # fallback


def test_no_arg_compatibility_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    tree = mounter.mount(SampleWorktree)  # initial_states=None
    
    assert tree.config1.username == "default_user"
    assert tree.config1.port == 8080
    assert tree.config2.username == "default_user"
    assert tree.config2.port == 8080
    assert tree.layout.config3.username == "default_user"
    assert tree.layout.config3.port == 8080


def test_required_fields_with_initial_states_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    # Succeeds if required fields are provided
    tree = mounter.mount(
        RequiredWorktree,
        initial_states={
            "config": {"required_key": "provided_value"}
        }
    )
    assert tree.config.required_key == "provided_value"
    
    # Raises MissingInitialStateError if omitted
    with pytest.raises(MissingInitialStateError) as exc_info:
        mounter.mount(RequiredWorktree)
        
    assert "Missing required fields: required_key" in str(exc_info.value)
    assert exc_info.value.item_name == "config.required_key"
    assert exc_info.value.__cause__ is not None  # ValidationError


def test_non_pydantic_exception_propagation_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    # Succeeds if the custom item gets its required value
    tree = mounter.mount(
        NonPydanticWorktree,
        initial_states={
            "mock_item": {"required_val": "some-value"}
        }
    )
    assert tree.mock_item.val == "some-value"
    
    # Raises MissingInitialStateError if omitted
    with pytest.raises(MissingInitialStateError) as exc_info:
        mounter.mount(NonPydanticWorktree)
        
    assert "mock_item.required_val" in str(exc_info.value)
    assert "required_val is missing" in str(exc_info.value)
    assert exc_info.value.item_name == "mock_item.required_val"


def test_non_pydantic_raw_exception_wrapping_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)
    
    # Raises MissingInitialStateError wrapping the raw ValueError
    with pytest.raises(MissingInitialStateError) as exc_info:
        mounter.mount(NonPydanticRawErrorWorktree)
        
    assert "mock_item_raw" in str(exc_info.value)
    assert "raw initialization issue" in str(exc_info.value)
    assert exc_info.value.item_name == "mock_item_raw"
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_nested_required_fields_with_initial_states_e2e():
    driver = InMemoryMountDriver()
    root = driver.mount(NoMountpoint())
    mounter = BaseMounter(root)

    # Succeeds if the nested required field is provided
    tree = mounter.mount(
        RequiredNestedWorktree,
        initial_states={
            "layout": {
                "config3": {"required_field": "provided_nested_value"}
            }
        }
    )
    assert tree.layout.config3.required_field == "provided_nested_value"

    # Raises MissingInitialStateError with correct layout.config3.required_field path when omitted
    with pytest.raises(MissingInitialStateError) as exc_info:
        mounter.mount(
            RequiredNestedWorktree,
            initial_states={
                "layout": {
                    "config3": {}
                }
            }
        )

    assert "Missing required fields: required_field" in str(exc_info.value)
    assert exc_info.value.item_name == "layout.config3.required_field"
    assert exc_info.value.__cause__ is not None  # ValidationError
