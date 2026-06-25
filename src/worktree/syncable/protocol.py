from worktree.decorators import not_implemented


#todo move this to worktree package as standalone module

class Syncable:
    @not_implemented
    def sync(self):
        """
        Downstream synchronization - from persistent or initialized form to memory.
        """

    @not_implemented
    def commit(self):
        """
        Upstream synchronization - from memory to persistent form.
        """