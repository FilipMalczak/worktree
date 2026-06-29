import json
from pathlib import Path
from typing import Self
 
from pydantic import BaseModel, TypeAdapter, ValidationError
 
from worktree.contract import Artifact, MissingInitialStateError
from worktree.mounting.accessible import Collection, Object
from worktree.mounting.claim import Claim, ObjectClaim
from worktree.decorators import unreachable_worktree_action
 
 
class PydanticArtifact(BaseModel, Artifact[Self]):
    """
    An in-memory piece of persistent data represented as a Pydantic model and backed by a single object with JSON contents.
 
    The mount path of the artifact is derived solely from the item name suffixed with `.json`.
 
    Subclasses must define:
        1. Pydantic fields with default values or default factories.
 
    Important Constraints:
        - All defined fields MUST have default values or default factories. Direct instantiation using field values
          (e.g., `MyModel(field=val)`) is not supported. Instead, instances are instantiated via `MyModel(mounted_at)`
          and initialized with defaults, which are then synchronized with the storage back-end.
    """
 
    def __init__(
        self,
        item_name: str,
        mounted_at: Collection | None = None,
        initial_states: dict | None = None,
        **kwargs
    ):
        """
        Initialize the Pydantic model and register it within the worktree collection.
 
        Accepts arbitrary keyword arguments for Pydantic cooperative inheritance validation and model reconstruction.
        """
        pydantic_kwargs = initial_states or {}
        try:
            BaseModel.__init__(self, **{**pydantic_kwargs, **kwargs})
        except ValidationError as e:
            missing_fields = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
            if missing_fields:
                missing_str = ", ".join(str(f) for f in missing_fields)
                raise MissingInitialStateError(
                    item_name=str(missing_fields[0]),
                    message=f"Missing required fields: {missing_str}"
                ) from e
            raise
        self._item_name = item_name
        if mounted_at is not None:
            Artifact.__init__(self, item_name, mounted_at, initial_states=initial_states)

    # TODO: Set up subclass post-init to decorate initialize_object, validate_object, and commit_object
    #  to dynamically assert that they are called with a path matching the owned claims.
 
    @property
    def artifact_mount_path(self) -> str:
        return f"{self.item_name}.json"

    def ownership_claims(self) -> list[Claim]:
        """
        Declare ownership of the object at the mount path.
        """
        return [
            ObjectClaim(path=Path(self.artifact_mount_path))
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
        cls = type(self)
        original_init = cls.__init__
        cls.__init__ = BaseModel.__init__
        try:
            adapter = TypeAdapter(cls)
            validated = adapter.validate_json(txt)
        finally:
            cls.__init__ = original_init
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
