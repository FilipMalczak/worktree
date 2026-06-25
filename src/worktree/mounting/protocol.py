from typing import Protocol

from worktree.contract import Worktree


class Mounter(Protocol):
    def mount[Tree: Worktree](self, tree: type[Tree]) -> Tree: ...