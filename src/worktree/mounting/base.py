from dataclasses import dataclass

from worktree.contract import Worktree
from worktree.mounting.accessible import RootCollection
from worktree.mounting.protocol import Mounter


@dataclass(frozen=True)
class BaseMounter(Mounter):
    root: RootCollection

    def mount[Tree: Worktree](self, tree: type[Tree]) -> Tree:
        out = tree(self.root)
        out.sync()
        return out
