from dataclasses import dataclass

from src.worktree.contract import Worktree, WorktreeItem
from src.worktree.mounting.accessible import RootCollection
from src.worktree.mounting.protocol import Mounter

@dataclass(frozen=True)
class BaseMounter(Mounter):
    root: RootCollection

    def mount[Tree: Worktree](self, tree: type[Tree]) -> Tree:
        out = tree(self.root)
        out.sync()
