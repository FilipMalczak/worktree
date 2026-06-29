from dataclasses import dataclass
from typing import Any

from worktree.contract import Worktree
from worktree.mounting.accessible import RootCollection
from worktree.mounting.protocol import Mounter


@dataclass(frozen=True)
class BaseMounter(Mounter):
    root: RootCollection

    def mount[Tree: Worktree](self, tree: type[Tree], initial_states: dict[str, Any] | None = None) -> Tree:
        out = tree(self.root, initial_states=initial_states)
        out.sync()
        return out
