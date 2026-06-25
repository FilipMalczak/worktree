# worktree

> Worktree is a declarative runtime system for defining and synchronizing persistent Artifact graphs between memory and external backends, with explicit lifecycle control and composable state trees.

## Common rules

We do not use `typing.Protocol`s or `abc.ABC`s in the contract. 
Instead, we use plain Python classes and decorate abstract methods with `@not_implemented`.

Prefer `match` statements over `if`s. Rule of thumb: if you're using `elif`, you should be using `match` instead; otherwise, you're good.

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

### GIT

#### Staging

If you create new files that represent the work you're doing for me, stage them. 
Do not stage scratch files, experiments, one-shot tests that check how certain library behaves, etc.
Your goal is to stop at the point where I could commit the whole thing myself.

#### Commiting

Whenever you do any work, DO NOT commit unless either:
- I directly and explicitly ask you to, or
- you're executing a plan (that was reviewed by me, see above) that includes instructions to commit at some point.

I need to keep full control over what and when gets commited.

Whenever you want to commit but are stopped by the instructions above, ask me if you may do so. 
Provide proposed commit message and scope (list of files to commit) at that point.

### Testing

When testing mid-work, you're allowed to use any set of test case/suites/files.

When testing because you believe you've finished the work, ALWAYS run the whole `./tests/` suite.
NEVER stop working unless the whole `./tests` suite is green.

NEVER remove test cases or suites without explicit approval.  

#### E2E

We sometimes duplicate unit test suites with E2E suites. 
Unit tests validate code directly, e.g. tests for specific artifacts or anchors simulate how the mounted worktree would behave.
E2E tests mimic the checked scenarios, but they do so by setting up the whole stack, by mounting a worktree with a real mounter (usually in-memory one, outside of mounter implementations tests, which rarely get E2E suites).

When asked to produce E2E suite, you need to know which unit suite you're working off, then produce test file with `_e2e` suffix (`test_foo.py` -> `test_foo_e2e.py`). 
That new file should duplicate the unit test cases as much as possible, while staying in e2e mode. 
If a case cannot be duplicated, it must be noted as a comment in e2e suite file, ideally in matching place.

When duplicating test cases between unit and E2E suites, the E2E suite should reuse the mock, stub, and sample types defined in the unit test suite whenever possible.

