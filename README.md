# worktree

> Worktree is a declarative runtime system for defining and synchronizing 
> persistent Artifact graphs between memory and external backends, with explicit 
> lifecycle control and composable state trees.

If you run the following program for the first time, you will get "0" on stdout and the counter.json file in /data directory. If you rerun it, you'll be getting consecutive integers each time (and the file will change to track last printed number). 

```python
from worktree.contract import Worktree
from worktree.impl.items.pydantic_model import PydanticArtifact
from worktree.mounting.base import BaseMounter
from worktree.impl.accessibility.filesystem import FilesystemMountDriver

# Define an artifact mapping to a JSON object
class Counter(PydanticArtifact):
    number: int = 0

# Define a worktree containing the artifact
class CounterWorktree(Worktree):
    counter: Counter

# Instantiate the mount driver and mounter
driver = FilesystemMountDriver()
root = driver.mount("/data")
mounter = BaseMounter(root)

# Mount the worktree (performing downstream sync automatically)
worktree = mounter.mount(CounterWorktree)

# Print and increment
print(worktree.counter.number) 
worktree.counter.number += 1

# Commit changes back to "/data/counter.json"
worktree.commit()
```

Poor for scripting, poor for webservices, pretty awesome for agentic systems.


---

## Core Abstractions

Worktree bridges the gap between structured in-memory Python models and external, persistent storage backends. It is built around a few central abstractions:

* **`Syncable`**: The base contract defining the synchronization lifecycle:
  * `sync()`: Pulls/validates state from storage to the in-memory models; if no storage representation is present, initializes the state and commits it.
  * `commit()`: Writes the current in-memory state back to storage.
* **`Accessible` (`Object` | `Collection`)**: Abstractions representing storage nodes:
  * `Object` represents a file-like entry (supporting text and binary read/write operations).
  * `Collection` represents a directory-like entry (supporting resource creation, deletion, and traversal).
  
  > [!NOTE]
  > We intentionally avoid strict "file" or "directory" terminology. The underlying storage accesses are generic abstractions (`Object` and `Collection`) which can be implemented for any storage provider — such as AWS S3, databases, remote APIs, sandboxed virtual shells, or SQL DBs. While the codebase currently provides `Filesystem` and `InMemory` drivers, extending this to a new backend is straightforward.
* **`Claim` (`ObjectClaim` | `CollectionClaim`)**: Models resource ownership. Each `BaseWorktreeItem` declares which paths/files it claims to own.
* **`BaseWorktreeItem`**: A base class for concrete leaf items (such as `Artifact` or `Anchor`). It manages the state initialization, validation, and serialization logic for each declared claim during a sync or commit.
* **`Artifact[Value]` / `Anchor[Handle]`**:
  * `Artifact` has an in-memory representation (its `value()`).
  * `Anchor` controls resources with no direct in-memory representation (exposing a `handle()`).
  > [!NOTE]
  > If you use the filesystem storage driver, then `Artifact.value()` usually represents the loaded contents of a file, while `Anchor.handle()` models a path to the managed directory.
  > The distinction is meant to help us avoid representing actual data as indirect pointers or producing specialized abstractions over structures that are not meant to live in memory.
* **`Worktree`**: A composable class containing other `WorktreeItem`s. Sub-worktrees can run in sub-collections (directories) recursively.

---

## Layout Anchors and Nested Configurations

For more complex directory structures, you can use a `LayoutAnchor` to organize collections without creating synchronization boundaries.

`LayoutAnchor` allows you to nest other layout anchors and artifacts using standard field annotations or nested inner classes:

```python
from worktree.contract import Worktree, LayoutAnchor
from worktree.impl.items.pydantic_model import PydanticArtifact
from worktree.mounting.base import BaseMounter
from worktree.impl.accessibility.filesystem import FilesystemMountDriver

# Define artifacts
class DatabaseConfig(PydanticArtifact):
    host: str = "localhost"
    port: int = 5432

class ServerConfig(PydanticArtifact):
    debug: bool = False

# Define a layout with nested layouts and artifacts
class AppLayout(LayoutAnchor):
    # Defining a nested layout using an inner class
    class Storage(LayoutAnchor):
        db: DatabaseConfig
    
    # Declare fields matching the layout structure
    storage: Storage
    config: ServerConfig
    logs: LayoutAnchor  # Bare directory/collection stub

class ProjectWorktree(Worktree):
    app: AppLayout

# Mount and synchronize
driver = FilesystemMountDriver()
root = driver.mount("/data")
mounter = BaseMounter(root)
tree = mounter.mount(ProjectWorktree)

# Access deep-nested properties directly
print(tree.app.storage.db.host)  # prints "localhost" on first run, but "postgres.prod" on consecutive ones (see following lines)
print(tree.app.config.debug)     # prints False

# Modify nested values
tree.app.storage.db.host = "postgres.prod"
tree.commit()  # Recursively commits all modified artifacts
```

---

## Synchronization Lifecycle

### Downstream Synchronization (`sync`)
For each claim defined by `ownership_claims()`:
1. Checks if the resource exists at the claimed path within its mounted collection.
2. **If missing**:
   - Touches/mkdir-s the target resource.
   - Runs `initialize_object` / `initialize_collection` (sets up default field states).
   - Performs an initial `commit_object` / `commit_collection` to write defaults to storage.
3. **If present**:
   - Runs `validate_object` / `validate_collection` to load the stored content and validate/populate in-memory fields.

### Upstream Synchronization (`commit`)
For each claim:
1. Retrieves the stored resource (asserting it exists).
2. Executes `commit_object` / `commit_collection` to write current in-memory field values back to storage.

---

## Development

We use `uv` for python dependency and environment management.

### Installation
Clone the repository and install dependencies:
```bash
uv sync
```

### Running Tests
Execute the test suite (covering unit and E2E scenarios):
```bash
uv run pytest
```
