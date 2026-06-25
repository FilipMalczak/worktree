# Worktree System Summary

Worktree is a declarative runtime system for defining and synchronizing persistent Artifact graphs between memory and external backends, with explicit lifecycle control and composable state trees.

---

## 1. Core Concepts & Architecture

The system revolves around synchronizing a declarative, in-memory state tree (represented by Python classes and fields) with a corresponding storage layer (represented by file-system directories or custom backends).

```mermaid
graph TD
    Mounter[Mounter / BaseMounter] -->|mounts| Worktree[Worktree Class]
    Worktree -->|has fields| WorktreeItem[WorktreeItem: Artifact | Anchor | Worktree]
    WorktreeItem -->|claims| Claim[Claim: ObjectClaim | CollectionClaim]
    WorktreeItem -->|manages| RootCollection[RootCollection / AgnosticCollection]
    
    RootCollection -->|Filesystem| FilesystemCollection[FilesystemCollection]
    RootCollection -->|In-Memory| InMemoryCollection[InMemoryCollection]
```

### Key Components

- **`Syncable`**: The base contract defining the synchronization lifecycle:
  - `sync()`: Pulls/validates state from the backend storage to the in-memory models.
  - `commit()`: Writes the current in-memory model state back to the backend storage.
- **`Accessible` (`Object` | `Collection`)**: Abstractions for the storage layer:
  - `Object` represents a file (supporting text and binary read/write operations).
  - `Collection` represents a directory (supporting file creation, deletion, searching, and traversal).
- **`Claim` (`ObjectClaim` | `CollectionClaim`)**: Models the resource ownership requirements of `BaseWorktreeItem` subclasses. They declare the relative path and target type (file or folder) they claim to own.
- **`BaseWorktreeItem`**: A base class for concrete leaf items (such as `Artifact` or `Anchor`). It manages the state initialization, validation, and serialization logic for each declared claim during a sync or commit.
- **`Artifact[Value]` / `Anchor[Handle]`**:
  - `Artifact` has an in-memory representation (its `value()`).
  - `Anchor` controls resources with no direct in-memory representation, exposing a `handle()`.
- **`Worktree`**: A composable class containing other `WorktreeItem`s. Fields are dynamically inspected and instantiated via annotations, allowing sub-worktrees to run in sub-collections (directories) recursively.

---

## 2. Synchronization Lifecycle

Synchronization follows a strict, declarative pattern managed by `BaseWorktreeItem.sync()` and `BaseWorktreeItem.commit()`:

### Downstream Synchronization (`sync`)
For each claim defined by `ownership_claims()`:
1. The item checks if the resource exists at the claimed path within its mounted collection.
2. **If missing**:
   - It touches/mkdir-s the target resource.
   - It runs `initialize_object` / `initialize_collection` (sets up default field states).
   - It performs an initial `commit_object` / `commit_collection` to write the defaults to the storage.
3. **If present**:
   - It runs `validate_object` / `validate_collection` to load the stored content and validate/populate the in-memory fields.

### Upstream Synchronization (`commit`)
For each claim:
1. The item retrieves the stored resource (asserting it exists).
2. It executes `commit_object` / `commit_collection` to write current in-memory field values back to storage.

---

## 3. Module Breakdown

### `src/worktree/contract.py`
Defines the base synchronization interfaces (`BaseWorktreeItem`, `Artifact`, `Anchor`, `Worktree`) and reflective instantiation logic (`get_worktree_items`).

### `src/worktree/decorators.py`
Contains helper decorators:
- `@not_implemented`: Replaces standard abstract methods to fail at runtime with a clean error message.
- `@unreachable_worktree_action`: Used to mark methods that are out-of-scope for specific artifact types (e.g., calling collection methods on a file-only artifact).

### `src/worktree/mounting/`
- `accessible.py`: Declarations for file-like (`Object`) and directory-like (`Collection` / `AgnosticCollection`) nodes, and `MountDriver`.
- `claim.py`: Pydantic models for declaring file/directory path requirements (`ObjectClaim`, `CollectionClaim`).
- `base.py` / `protocol.py`: Defines the `Mounter` interface and `BaseMounter`, which constructs and synchronizes `Worktree` trees.

### `src/worktree/syncable/`
- `protocol.py`: Defines the base `Syncable` contract.

### `src/worktree/impl/`
- `items/pydantic_model.py`: Implements `PydanticArtifact`, which binds Pydantic models to JSON files (claims a single object at a configured `mount_path`, deserializing JSON contents in `validate_object` and writing JSON on `commit_object`).
- `accessibility/memory.py`: Implements `InMemoryMountDriver` and storage utilities (`InMemoryCollection`, `InMemoryObject`) for fast unit tests.
- `accessibility/filesystem.py`: Implements `FilesystemMountDriver` and physical storage utilities (`FilesystemCollection`, `FilesystemObject`).

---

## 4. Test Structure

Tests are located in `tests/` and cover different levels of validation:
- **`test_mount_drivers.py`**: Validates the driver operations (`exists`, `touch`, `mkdir`, `read_text`, `write_text`, `rm`, `ls`) using a shared suite run against both `FilesystemMountDriver` and `InMemoryMountDriver`.
- **`test_pydantic_artifact.py`**: Unit tests verifying the synchronization lifecycle of `PydanticArtifact` (initial sync, loading existing files, committing changes, validation errors, and unreachable collection behaviors).
- **`test_pydantic_artifact_e2e.py`**: E2E tests validating the full workflow by loading the Pydantic artifacts through a mounted `SampleWorktree` using `BaseMounter` and checking state propagation.
