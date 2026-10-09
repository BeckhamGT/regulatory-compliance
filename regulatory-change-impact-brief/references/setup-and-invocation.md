# Setup and invocation

## Runtime choice

Use **Python 3.10 or newer on macOS or Linux (POSIX)** in a repository-local virtual environment. The engine uses `fcntl` to serialize mutations, so native Windows requires a POSIX environment such as WSL. JSON Schema validation uses `jsonschema`; RFC 5545 parsing uses `icalendar`. The standard library handles hashes, CSV, preservation, and command-line orchestration. The pinned dependency versions live in `scripts/requirements.txt`; read that file rather than maintaining a second dependency list here.

The host agent needs native read access to Notion and Google Sheets, plus a browser capable of reading the original public pages. It retrieves source responses through those tools and records them with the Python helper. This design preserves source access requirements without pretending that a shell process inherits desktop connector authentication.

Resolve the root and install only the isolated runtime:

```sh
git rev-parse --show-toplevel
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r regulatory-change-impact-brief/scripts/requirements.txt
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py --help
```

Run these commands from the verified repository root. If `python3` is older than 3.10, select an installed Python 3.10+ interpreter for `-m venv`; document the actual interpreter and version in the run report. Keep `.venv`, credentials, tokens, application configuration, and Entire working files out of Git. The skill bundle and captures contain no credentials.

Before implementation or a run, inspect:

```sh
codex --version
entire --version
entire status --detailed
entire session list
entire session current --json
```

Inspect the actual current-session transcript and checkpoint metadata with the inspection commands reported by `entire agent-help`. Verify matching session identity and nonzero token usage. Repository `Enabled` status alone does not establish that the current session is active or captured. Retain any ended-session or hook limitation honestly; use only supported recovery, not invented hook events or edited session metadata.

## End-to-end invocation

In the connected Agent Skills host, submit this single command:

```text
Read regulatory-change-impact-brief/SKILL.md and run it with interviews/project-b-regulatory-compliance-20261008-1603.md
```

This invokes the entire skill workflow: a new run, ten fresh live source routes, source-grounded analysis, deterministic outputs, and actual validation. It requires the native tools described above. On hosts that register repository bundles as named skills, the equivalent invocation is `$regulatory-change-impact-brief interviews/project-b-regulatory-compliance-20261008-1603.md`; registration must preserve the entire bundle and relative companion paths.

The following commands are internal steps, not substitutes for that end-to-end invocation:

```sh
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py begin --interview interviews/project-b-regulatory-compliance-20261008-1603.md
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py stage --sequence 3 --analysis deliverables/analysis.json
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py stage --sequence 4 --analysis deliverables/analysis.json
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py stage --sequence 5 --analysis deliverables/analysis.json
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py stage --sequence 6 --analysis deliverables/analysis.json
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py build --analysis deliverables/analysis.json
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py validate --json
```

After `begin`, perform every live acquisition and `record` each attempt using the exact CLI shown in `engine.py record --help`. Complete capture before closing stage 3; later source changes require a new run. Prepare the current `deliverables/analysis.json` from new captures and bind it to that run's manifest hash. Close stages 3, 4, 5, and 6 sequentially, adding each boundary's actual records before its `stage` command. Final `build` verifies those completed boundaries, renders final artifacts, and writes stage 7. A helper `build` using existing inputs is a deterministic render/check, not a new live review.

## Portable installation

Keep one authoritative bundle in this repository. For a runtime that requires registration elsewhere, use that runtime's supported project-skill registration or a link to this bundle. For a disposable forward test, copy the entire `regulatory-change-impact-brief/` directory into the isolated test runtime's skill directory, preserving the `SKILL.md` filename and all relative paths. Provide the test repository's README, unchanged schema, and canonical input separately; observe the registered skill and generated artifacts from a fresh session. Never edit the disposable copy as a second maintained home.

No environment-specific home directory is embedded in the shipped skill. A new clone needs its own isolated Python environment and native connector permissions. Facilitator verification of learner identity, interview provenance, capture, runtime access, and destination is a distinct external setup check; record it as unverified until actually obtained.
