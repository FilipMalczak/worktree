# worktree

> Worktree is a declarative runtime system for defining and synchronizing 
> persistent Artifact graphs between memory and external backends, with explicit 
> lifecycle control and composable state trees.

This is what we're aiming for:

```python

class Counter(JSONFile):
    number: int = 0


# or maybe XMLFile? or directory that requires specific set of subdirectories or 
# any other validators? or GIT submodule? or anything that can be both
# initialized and validated

class AnotherWorktree(Worktree):
    ...


class CounterWorktree(Worktree):
    counter = Counter.mount("./counter.json")
    another = AnotherWorktree.mount("./another")


backend = FilesystemBackend()

worktree = backend.sync(CounterWorktree, "/data")
# each time you execute the program without messing with ./data, the program will print consecutive integers
print(worktree.counter.number) 
worktree.counter.number += 1

worktree.commit()
```

Poor for scripting, poor for webservices, pretty awesome for agentic systems.
