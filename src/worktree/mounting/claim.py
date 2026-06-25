from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from worktree.mounting.accessible import ObjectType

ObjectClaimTarget = Literal["object"]
CollectionClaimTarget = Literal["collection"]
ClaimTarget = ObjectClaimTarget | CollectionClaimTarget

class ObjectClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    target: ObjectClaimTarget = "object"
    path: Path
    object_type: ObjectType = "text"


class CollectionClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    target: CollectionClaimTarget = "collection"
    path: Path


Claim = ObjectClaim | CollectionClaim