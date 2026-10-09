# Validation and recovery

## Inspect the actual run

Run `engine.py validate --json` with the isolated interpreter after rendering. Read the actual saved files even when the source versions appear unchanged. The validator is an integrity aid; the host must inspect whether the evidence supports the reasoning and whether every disclosed route/system/action is accounted for.

| Check | Required result |
|---|---|
| Original inputs | Interview and root schema remain unchanged; current identities/hashes recorded |
| Freshness | Every interview-disclosed route has a current-run live request/response time and attempt; all failures preserved |
| Capture integrity | Successful requested content is present and hashes match; failures without content retain null path/hash |
| Identity/version | Original source identity, exact native tab/range/article locators, observed dates and historical limits retained |
| Schema | All seven snapshots pass Draft 2020-12 schema with format checking |
| Chain | Shared run ID, sequence/stage correspondence, immediate predecessor path/ID/hash match actual bytes |
| Records | Produced IDs exist; consumed IDs come from upstream; evidence references and citations resolve |
| Legal blockers | Required unavailable/unsuitable authority withholds dependent conclusions and blocks normal publication |
| CSV | Exact header, stable distinct impact rows, valid states/dates, full system coverage and resolvable basis |
| Brief | Same run/status/impacts/actions/dates/limits; pending human decisions and uninspected proofs visible |
| Calendar | RFC 5545 parser succeeds; stable unique UIDs, tentative approval state, source-supported dates, exclusive end dates |
| Review bindings | Every request matches final artifact path/hash, run, version, subject and reviewer; brief has no self-hash |
| Final artifacts | Stage 07 path/hash and validation results match the actual files and stage 06 |

Record failed stage, source/output path, concrete error, recovery action, and responsible recovery owner. A successfully parsed file with unsupported conclusions is not a successful review. Report partial/blocked outputs honestly even when structural checks pass.

## Preserve and recover

Use a new `begin --interview ... --reason ...` for every new full run or recovery attempt. Before replacing current outputs, archive the actual prior run and captured sources under `deliverables/history/<prior-run-id>/`. Preserve existing history separately rather than recursively archiving the history directory into itself.

Record `supersedes_run_id` and the concrete reason in the new scope. Retain damaged prior files exactly as found with an integrity/failure note; missing prior files remain a recorded gap. Never manufacture an earlier run, corrected historical capture, approval, or successful output for display.

Archived records retain their original logical `deliverables/...` paths and hashes. Resolve those paths inside the preserved run's archive root, never against the current run. The archive manifest records physical locations, inventory hashes, and pre-archive validation. Inspect an archived bundle without rewriting its bytes:

```sh
.venv/bin/python regulatory-change-impact-brief/scripts/engine.py validate --history PRIOR_RUN_ID --json
```

Archive-integrity success means the retained bytes match what was archived; the separate package validation may still fail when the prior output was already damaged. Preserve both results.

Recompute from the earliest changed basis. A source-content/version change can affect authority, facts, impacts, actions, request hashes and all later stages. A damaged final output may reuse only verified current-run reasoning for a deterministic repair, but the accepted **full review recovery** begins a new run and freshly retrieves all ten routes. Re-run validation and inspect the actual output before reporting recovery.

Unchanged source content still gets new actual retrieval times and new run/snapshot IDs. Hash equality means equal captured bytes, not that a live request took place; preserve request receipts independently.

## Meaningful differential tests

Run the executable suite shipped as `scripts/test_engine.py`:

```sh
.venv/bin/python -m unittest discover -s regulatory-change-impact-brief/scripts -p 'test*.py' -v
```

Keep fixture-based tests distinct from the production live run. Inspect synthetic fixture inputs and resulting errors/artifacts; do not relabel them as actual source attempts. Exercise:

1. Reordered headers and rows, extra columns, and legitimate newer versions. Semantic IDs and findings remain stable; the fixed review date remains August 26, 2026, and version/history limits update.
2. Missing/ambiguous required fields, duplicate conflicting IDs, invalid dates/statuses, and dangling cross-register references. These become explicit invalid/unresolved records rather than guessed repairs.
3. An unavailable required legislative source. Dependent legal findings are withheld, the chain and brief/CSV are blocked, and calendar proposals are empty or limited to supported nondependent actions.
4. Tampered captures, manifests, citations, predecessor bytes, final outputs, and request hashes. Validation must detect the specific integrity failure, not merely assert that files exist.
5. Recovery from an actual damaged output in an isolated workspace. Preserve the actual prior damaged bundle, give the retry a new run ID, record supersession/failure owner, and produce newly validated artifacts.
6. Analysis from a different run or altered manifest. Reject it before rendering stale conclusions.

For the complete workflow, also run a real fresh-source invocation, inspect all actual resulting files, and perform an actual retry when a real failure occurs. Archive the real prior run. An offline suite cannot prove native connector access or live retrieval.

## Independent forward test

Copy the complete bundle into a disposable Agent Skills runtime and provide the paired baseline input without the expected result or the author's conclusions. Have a fresh agent follow the installed `SKILL.md`, inspect generated files, and report behavior. Give only minimal raw artifacts and permitted side effects. Review the outcome against `eval/baseline-output.md`, then correct only demonstrated defects. Do not let a fixture test contact reviewers or publish to Classroom.

Before committing, inspect the entire bundle for source instructions, credential leakage, unsafe external mutation, absolute environment paths, and detached companions. Run the available pinned skill scanner according to its installed guidance, and inspect its findings manually. Report scanner setup limitations separately; a clean scan is not proof of safe behavior.
