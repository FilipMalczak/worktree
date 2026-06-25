import json
from pathlib import Path
from typing import Self, ClassVar

from pydantic import BaseModel, TypeAdapter

from worktree.contract import Artifact
from worktree.mounting.accessible import Collection, Object
from worktree.mounting.claim import Claim, ObjectClaim
from worktree.decorators import unreachable_worktree_action


class PydanticArtifact(BaseModel, Artifact[Self]):
    """
    An in-memory piece of persistent data represented as a Pydantic model and backed by a single object with JSON contents.

    Subclasses must define:
        1. `mount_path: ClassVar[str]`: The relative path/filename of the JSON object within the collection.
        2. Pydantic fields with default values or default factories.

    Important Constraints:
        - All defined fields MUST have default values or default factories. Direct instantiation using field values
          (e.g., `MyModel(field=val)`) is not supported. Instead, instances are instantiated via `MyModel(mounted_at)`
          and initialized with defaults, which are then synchronized with the storage back-end.
    """
    mount_path: ClassVar[str]

    def __init__(self, mounted_at: Collection | None = None, **kwargs):
        """
        Initialize the Pydantic model and register it within the worktree collection.

        Accepts arbitrary keyword arguments for Pydantic cooperative inheritance validation and model reconstruction.
        """
        BaseModel.__init__(self, **kwargs)
        if mounted_at is not None:
            Artifact.__init__(self, mounted_at)

    # 2. Enforce the rule at runtime
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Check if the subclass defined the required variable
        if not hasattr(cls, 'mount_path'):
            raise NotImplementedError(
                f"Error: Subclass '{cls.__name__}' must define a `mount_path` class-level variable!"
            )
        # TODO: Enhance subclass post-init to decorate initialize_object, validate_object, and commit_object
        # to dynamically assert that they are called with a path matching the owned claims.

    def ownership_claims(self) -> list[Claim]:
        """
        Declare ownership of the object at the configured `mount_path`.
        """
        return [
            ObjectClaim(path=Path(type(self).mount_path))
        ]

    def initialize_object(self, path: Path, obj: Object):
        """
        Initialize a newly created object.

        For PydanticArtifact, the object is initialized with the default values specified in the Pydantic model fields.
        This method assumes it is called on an owned claim.
        """
        # TODO: Enhance class post init to decorate this method to assert it is called on an owned claim.

    def validate_object(self, path: Path, obj: Object):
        """
        Read the JSON object and validate/update the in-memory model fields with the object's values.
        This method assumes it is called on an owned claim.
        """
        # TODO: Enhance class post init to decorate this method to assert it is called on an owned claim.
        txt = obj.read_text()
        adapter = TypeAdapter(type(self))
        validated = adapter.validate_json(txt)
        fields = validated.model_dump(mode="python")
        for name, val in fields.items():
            setattr(self, name, val)

    def commit_object(self, path: Path, obj: Object):
        """
        Serialize the in-memory model fields to JSON and write them back to the persistent object.
        This method assumes it is called on an owned claim.
        """
        # TODO: Enhance class post init to decorate this method to assert it is called on an owned claim.
        data = self.model_dump(mode="json")
        txt = json.dumps(data)
        obj.write_text(txt)

    @unreachable_worktree_action(since="PydanticArtifact only claims objects, not collections")
    def initialize_collection(self, path: Path, collection: Collection): ...

    @unreachable_worktree_action(since="PydanticArtifact only claims objects, not collections")
    def validate_collection(self, path: Path, collection: Collection): ...

    @unreachable_worktree_action(since="PydanticArtifact only claims objects, not collections")
    def commit_collection(self, path: Path, collection: Collection): ...

    def value(self) -> Self:
        """
        Return the in-memory model instance itself.
        """
        return self
