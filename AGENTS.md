# worktree

> Worktree is a declarative runtime system for defining and synchronizing persistent Artifact graphs between memory and external backends, with explicit lifecycle control and composable state trees.

## Common rules

We do not use `typing.Protocol`s or `abc.ABC`s in the contract. 
Instead, we use plain Python classes and decorate abstract methods with `@not_implemented`.

## Operations

We're using `uv`.

Run tests: `uv run pytest`.
Run some python code: `uv run python`.

We're using python 3.14.

We're using pydantic extensively.

## Coding agents

### Planning

If you are an agent like Antigravity and you are running in Plan mode, NEVER execute the plan until explicitly asked to do so.
Explicit approval is usually given by clicking "Proceed" button.
In rare cases it might be stated as a simple, but very explicit message. 
Review message is never an approval.

### Commiting

Whenever you do any work, DO NOT commit unless either:
- I directly and explicitly ask you to, or
- you're executing a plan (that was reviewed by me, see above) that includes instructions to commit at some point.

I need to keep full control over what and when gets commited.

Whenever you want to commit but are stopped by the instructions above, ask me if you may do so. 
Provide proposed commit message and scope (list of files to commit) at that point. 