---
name: project-mechanics
description: Project-specific build/test/lint/typing commands for this repo. Read this skill at the start of any phase that runs validation (`stoker-work`, `stoker-fixup`, `stoker-rebase`).
---

# Project mechanics

This file is the source of truth for how this repo runs tests, lint,
and type-checking. Profile-shipped phase skills read it at the start
of each phase and use the named commands verbatim.

## Test commands

- `focused_test`: `uv run --only-group=nox nox -s test -- tests/foo_test.py::test_bar`
- `complete_test`: `uv run --only-group=nox nox -s test`

The `test` session spins up a Kafka testcontainer and sets the
required env vars (UNFURLBOT_*, KAFKA_*), so run focused tests through
nox rather than `uv run pytest` directly. Pass the specific test path
after `--`.

## Lint

- `lint_touched`: `uv run --group=lint pre-commit run --files {files}`
- `lint_all`: `uv run --only-group=nox nox -s lint`

## Typing

- `typing`: `uv run --only-group=nox nox -s typing`

## Final validation

End-of-task validation runs `uv run --only-group=nox nox -s test` +
`uv run --only-group=nox nox -s lint` +
`uv run --only-group=nox nox -s typing` in that order, in the
foreground. The Docker image build is CI's responsibility, not the
in-iteration gate. Plus `uv run --only-group=nox nox -s docs` when
`docs/` changes.

<!-- stoker-onboarded-from: github.com/lsst-sqre/rubin-stoker//profile@main
     prompt-hash: 348ec538f8f7f6fa42da3569d855eab629174668ef28ea225f8b37511daac9d4
     onboarded-at: 2026-06-19T13:27:42Z -->
