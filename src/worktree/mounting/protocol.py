from worktree.contract import Worktree
from worktree.decorators import not_implemented


class Mounter:
    @not_implemented
    def mount[Tree: Worktree](self, tree: type[Tree]) -> Tree: ...