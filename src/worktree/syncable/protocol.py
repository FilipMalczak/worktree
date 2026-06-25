from typing import Protocol, runtime_checkable


#todo move this to worktree package as standalone module

@runtime_checkable
class Syncable(Protocol):
    def sync(self):
        """
        Downstream synchronization - from persistent or initialized form to memory.
        """

    def commit(self):
        """
        Upstream synchronization - from memory to persistent form.
        """