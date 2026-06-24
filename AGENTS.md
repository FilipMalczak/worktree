# worktree

> Worktree is a declarative runtime system for defining and synchronizing persistent Artifact graphs between memory and external backends, with explicit lifecycle control and composable state trees.

## Common rules

We use `typing.Protocol`s extensively in the contract.
We very rarely (to the point of "never") use `abc.ABC` - we wanna avoid metaclass issues in the future.

> TODO Protocols have metaclasses too; lets just make everything plain python classes and make abstract methods raise by default (decorators ftw)

## Operations

We're using `uv`.

Run tests: `uv run pytest`.
Run some python code: `uv run python`.

We're using python 3.14.

We're using pydantic extensively.

## Agentic planning

If you are an agent like Antigravity and you are running in Plan mode, NEVER execute the plan until explicitly asked to do so. Explicit approval is usually given by clicking "Proceed" button. In rare cases it might be stated as a simple, but very explicit message. Review message is never an approval.