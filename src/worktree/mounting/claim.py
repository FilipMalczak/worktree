from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

ObjectClaimTarget = Literal["object"]
CollectionClaimTarget = Literal["collection"]
ClaimTarget = ObjectClaimTarget | CollectionClaimTarget

class ObjectClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    target: ObjectClaimTarget = "object"
    path: Path


class CollectionClaim(BaseModel):
    model_config = ConfigDict(frozen=True)
    target: CollectionClaimTarget = "collection"
    path: Path


Claim = ObjectClaim | CollectionClaim