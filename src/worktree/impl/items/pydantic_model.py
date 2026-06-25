import json
from pathlib import Path
from typing import Self, ClassVar

from pydantic import BaseModel, TypeAdapter

from worktree.contract import Artifact
from worktree.mounting.accessible import Collection, Object, TextObject
from worktree.mounting.claim import Claim, ObjectClaim


class PydanticArtifact(BaseModel, Artifact[Self]):
    mount_path: ClassVar[str]

    def __init__(self, mounted_at: Collection):
        super(BaseModel, self).__init__()
        super(Artifact, self).__init__(mounted_at)

    # 2. Enforce the rule at runtime
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Check if the subclass defined the required variable
        if not hasattr(cls, 'mount_path'):
            raise NotImplementedError(
                f"Error: Subclass '{cls.__name__}' must define a `mount_path` class-level variable!"
            )

    def ownership_claims(self) -> list[Claim]:
        return [
            ObjectClaim(path=type(self).mount_path)
        ]

    def initialize_object(self, path: Path, obj: TextObject):
        assert path == type(self).mount_path #fixme better exception
        #otherwise, pydantic model is already initialized; all fields must have defaults, otherwise this

    def validate_object(self, path: Path, obj: TextObject):
        assert path == type(self).mount_path  # fixme better exception
        txt = obj.read()
        loaded = json.loads(txt)
        adapter = TypeAdapter(type(self))
        validated = adapter.validate_json(loaded)
        fields = validated.model_dump(mode="python")
        for name, val in fields.items():
            setattr(self, name, val)

    def commit_object(self, path: Path, obj: TextObject):
        assert path == type(self).mount_path  # fixme better exception
        data = self.model_dump(mode="json")
        txt = json.dumps(data)
        obj.write(txt)

    # should never attempt to work on any collection
    def initialize_collection(self, path: Path, collection: Collection):
        assert False # fixme better exception

    def validate_collection(self, path: Path, collection: Collection):
        assert False  # fixme better exception

    def commit_collection(self, path: Path, collection: Collection):
        assert False  # fixme better exception

    def value(self) -> Self:
        return self

