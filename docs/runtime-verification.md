# Runtime and capture verification

Observed on October 8, 2026 in this repository:

- Codex CLI: `0.161.0`; the current desktop session's original metadata reports CLI `0.160.0` at its start. These are distinct observations.
- Entire CLI: `0.11.3`.
- Current Codex session: `01a119a7-4b5a-7e51-9f85-3052f186d5ba`.
- Implementation interpreter: Python `3.12.14` on macOS, selected from the desktop's bundled runtime; dependencies installed into the repository's ignored `.venv`. The helper supports POSIX macOS/Linux because mutations use `fcntl` file locking; native Windows needs a POSIX environment such as WSL.
- Runtime libraries: jsonschema `4.25.1`, icalendar `6.3.2`; PyYAML `6.0.2` supports skill packaging validation.

The connected Codex desktop agent performs the native live reads. A shell process does not inherit its Notion or Sheets connector authentication. The deterministic Python engine preserves evidence, checks records and hashes, and renders drafts. The skill documents its complete agent invocation and the isolated setup needed in a new clone.

Entire remains enabled, with Git and Codex hooks installed and approved. After an interrupted turn, `entire doctor` reported a stale exited process record and recommended discarding that record. No forced discard, invented hook event, or transcript edit was performed. The actual session transcript continued to grow with current tool activity and nonzero token-usage records. Final checkpoint inspection must verify the real transcript and token usage; enabled status alone is insufficient. Supported `entire session attach` may be used to preserve the actual transcript if the commit hooks do not capture it.

On October 9 at approximately 02:00 UTC (October 8 local time), after the user resumed the task, `entire status --detailed` and `entire session current --json` reported this same session as **active**, with the current continuation prompt. The live session counter still reported zero tokens before checkpoint creation. This is distinct from the earlier ended/stale metadata and does not replace the required committed-transcript and nonzero checkpoint-token verification.

The original setup checkpoint and interview checkpoint were separately verified and pushed before implementation. Their historical observations remain in `docs/setup-check.md`. Facilitator verification of learner identity, interview provenance, capture, source access, and destination has not been supplied; this remains an external setup limitation. No official reviewer response or Classroom submission is implied by local validation or a GitHub push.
