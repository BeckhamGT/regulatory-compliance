# Reasoning and outputs

## Seven connected boundaries

Write the corresponding snapshot when a boundary is completed. Each snapshot uses the unchanged root `snapshot.schema.json`, a unique snapshot ID, the shared new run ID, meaningful consumed/produced record IDs, unresolved records, decisions, and actual state values. Sequence 1 has a null predecessor; each later sequence hashes the exact immediately preceding snapshot bytes.

`begin` writes scope; each `record` updates the capture boundary before downstream analysis starts. Close stages 3–6 with `engine.py stage --sequence N --analysis deliverables/analysis.json` when that boundary's analysis is complete. Each closure consumes only then-available upstream records. Final `build` requires completed stages 1–6, rejects changed already-closed stage arrays, and writes final artifacts before stage 7. Do not write retrospective stage placeholders only after producing the final outputs.

| Boundary | Required file | State that downstream work consumes |
|---|---|---|
| Scope | `deliverables/snapshots/01-scope.json` | Fixed review date, review type, scoped systems, recipients, approval gates, input identities, prior run and reason |
| Capture | `deliverables/snapshots/02-source-capture.json` | All current-run source attempts, versions, suitability, evidence paths/hashes, failures and limits |
| Authority/timing | `deliverables/snapshots/03-authority-and-timing.json` | Binding rules, timing rules, guidance context, authority blockers |
| Reconciliation | `deliverables/snapshots/04-evidence-reconciliation.json` | System facts, policy controls, incidents, conflicting evidence, factual gaps |
| Impacts | `deliverables/snapshots/05-impact-analysis.json` | Distinct system/rule findings, supported-no-impact items, conflicts, unresolved questions |
| Actions/reviews | `deliverables/snapshots/06-actions-and-approvals.json` | Proposed actions, review requests, approval requirements, escalations |
| Publication/checks | `deliverables/snapshots/07-publication-validation.json` | Exact final artifact paths/hashes, detached request bindings, actual validation checks, draft publication status |

Each record has `id`, `summary`, and `evidence_ids`. Make identifiers stable for the same semantic system/rule/action across changed input ordering, while snapshot and run IDs remain new. Produced IDs must exist in that boundary's state. Consumed IDs must exist in preceding boundaries; do not invent unused placeholder IDs merely to satisfy the schema. Substantive record fields contain actual values, not only a narrative that work occurred.

## Evidence-based authority and timing

For every rule proposition identify the exact paragraph, actor, duty, triggering behavior, output/exposure, exception, relevant commencement/application date, and evidence cited. Keep the original legal rule, amendment operation, dated consolidation, and guidance explanation distinguishable. Compare them; record contradictory wording or paragraph references with both citations and the source hierarchy used to choose a draft interpretation.

Use binding legislative content to support legal propositions. LAW and consolidation may reproduce authoritative paragraphs while their explanatory/documentary parts remain separate. Never elevate advisory TIME/FAQ summaries over an operative act. Keep dates for enactment, publication, entry into force, application, and any transition distinct. A provider-product transition must be evaluated against the actual actor/duty and supported product facts; it must not silently waive a deployer's separate duties.

When relevant binding text or timing cannot be retrieved or is unsuitable for the review date, record an authority blocker. Withhold dependent legal conclusions, publish unresolved rows and a blocked brief, and restrict the calendar to supported nondependent proposals. A blocked legal chain cannot end with normal `publication_status: validated`.

## Company evidence reconciliation

For each registered system reconcile the role, current behavior, exposed group, output type, notice, human review, provenance, exception status, and the dated evidence behind those facts. Join native registers by explicit stable IDs. Preserve the original row fields, locators, owner, and version in the record.

Treat an internal operating clarification as reported contextual facts with its own authorship and observation dates. Distinguish it from the policy's control requirements and from an actual inspected screenshot, export test, provider questionnaire, or release record. A referenced artifact name is not proof that its contents were retrieved. Record the uninspected referenced artifact and the resolution owner.

Preserve both sides of contradictions. A source's `complete`, `closed`, `planned`, `scheduled`, or `open` status does not establish a legal determination or approval. Missing factual fields, uncertain roles, stale evidence, unverified historical versions, and absent exception approval remain visible records with a named resolver where known. Human review of a flag does not by itself establish that biometric or other triggering functionality is absent.

## Analysis input contract

Create `deliverables/analysis.json` from current-run captures. Bind it with the exact `run_id` and `manifest_sha256` (`sha256:` plus the SHA-256 of `deliverables/sources/manifest.json`). The deterministic helper rejects analysis for another run or an altered manifest.

Top-level fields are `status`, `scope`, the record arrays below, `decisions`, and `limitations`, in addition to the binding fields. Scope includes `systems_in_scope`, `audiences`, `approval_gates`, and `review_type`.

| Arrays | Required substance |
|---|---|
| `binding_rules`, `timing_rules`, `guidance_context`, `authority_blockers` | Exact operative rules/dates and limitations |
| `system_facts`, `policy_controls`, `incident_evidence`, `conflicts`, `evidence_gaps` | Reconciled company evidence and preserved contradictions |
| `impacts`, `unaffected_items` | Distinct system/rule proposals, reasons, evidence, unknowns |
| `proposed_actions`, `approval_requirements`, `escalations` | Proposed owner/date/basis, matched commitments, human decisions and resolution needs |
| `decisions` | Concern, options, source basis, chosen behavior, rationale, tradeoffs, downstream effect |

Each substantive fact/rule includes `citations: [{"source_id": "CURRENT_SOURCE_ID", "locator": "article/paragraph or tab/row", "quote": "exact captured claim text"}]`. The quote must occur in that capture; this checks textual grounding, not the correctness of an interpretation. Use enough quoted context for the claim and preserve uncertainty in the record. Citing a source ID without claim-level support is insufficient for a substantive finding.

Impacts include `system_id`, `rule_ref`, `state`, `reason`, `owner`, `proposed_action`, `proposed_due_date`, and `approval_status`. Use exactly these finding states:

- `supported-impact`: sourced actor/behavior facts support a draft impact; human interpretation remains pending.
- `supported-no-impact`: sourced facts support a bounded no-impact proposal for this rule, not a blanket compliance certificate.
- `conflicting`: retained source evidence materially disagrees.
- `unresolved`: missing or unsuitable authority/facts prevent a supported conclusion.

Use empty owner/date fields where unknown, and explain the missing value. Do not infer due dates by adding an arbitrary offset to the run date. Existing calendar dates remain sourced proposed commitments, even when earlier than the actual retrieval date; preserve the fixed retrospective review basis.

Actions include `action_id`, `system_id`, `action`, `owner`, `due_date`, original `status`, `approval_required`, `impact_ids`, and `source_version`. Reuse an existing action ID when the subject is the same; retain every existing action, including general review actions. Explain any undated action omitted from the calendar.

Link each impact's proposal to its stage 06 actions through `impact.action_ids` or `action.impact_ids`. Linked systems must agree, and an impact's proposed date must match a linked action's sourced date.

## Human review requests and feedback

Each approval requirement is a record with `status: pending` and includes:

- A stable `request_id` and the relevant system, impact, or action subjects.
- The current `run_id`, source versions and evidence IDs.
- The exact question and required authorized reviewer role.
- An explicit unsent/delivery state; the workflow does not imply a request was delivered.

In this helper's request contract, `source_versions` is an object mapping each retrieved source ID in that request's transitive evidence dependencies to its exact `content_hash` from the current manifest. Include every retrieved dependency; never use a native revision label or policy date as the hash value. The manifest and records retain native `version_metadata` separately. Unavailable attempts have no content hash and are not entries in this map; the analysis and detached bindings also bind the exact manifest hash, preserving those failed attempt records as part of the reviewed run.

Legal retains final applicability/interpretation and exception decisions. Operations retains policy activation, approved deadlines/review dates, and incident closure. Owners resolve factual gaps. A proposal may recommend a next action while these decisions remain pending.

Write the final draft artifacts first. Then record detached bindings in stage 07: each review request points to the exact final artifact path and SHA-256. The brief references the binding location; it must not embed its own hash, which would create a circular dependency. Any draft change invalidates its earlier binding.

Accept reviewer feedback only through the facilitator-verified channel and with actual reviewer identity/role, request ID, subject, run/draft version or hash, decision time, outcome, and reasons/conditions. Verify the exact binding before applying feedback. Unknown identity, stale hashes, unmatched subjects, informal source notes, and unverified channels remain unresolved feedback. Never fabricate reviewer replies or convert a draft exception into an approval.

The shipped draft workflow does not send requests or ingest/activate approvals through an external endpoint. Until a verified feedback channel and matching validation adapter are actually configured, report that setup as missing and retain all decisions pending. A future authorized feedback path must validate the bindings above before changing status; the existence of binding metadata does not mean the channel is operational.

## Final formats and agreement

`impact-register.csv` has this header in this order:

```text
impact_id,system_id,rule_ref,state,evidence_ids,reason,owner,proposed_action,proposed_due_date,approval_status
```

Use one row per distinct system/rule impact or unresolved question. CSV quoting must preserve commas/newlines. Dates are `YYYY-MM-DD`; pending unknown fields are empty with a reason. Evidence IDs must resolve to the captured/derived chain.

`compliance-brief.md` identifies run ID, assigned as-of date, Legal/Operations recipients, draft/run status, source-quality limits, supported observations, conflicts/unresolved scope, actions/dates, and human decisions requested. Cite the relevant impact/action/evidence IDs. Include source version/history limits, unsent requests, and omitted undated actions. A validation result is a statement about the draft's internal consistency, never human approval.

`action-calendar.ics` uses RFC 5545 `VCALENDAR`, `VERSION:2.0`, and `PRODID`. Each dated proposed action has a stable action-based `UID`, actual UTC `DTSTAMP`, `DTSTART`, `SUMMARY`, and `DESCRIPTION` containing action/system/owner/reviewer, source/decision basis and approval state. Use `STATUS:TENTATIVE` for proposed dates. All-day events use `VALUE=DATE`; `DTEND`, when present, is the next day because it is exclusive. Escape property text and fold lines correctly. A source-dependent blocked action receives no unsupported commitment. Produce a valid empty calendar when no supported dated proposal exists.

Write stage 07 after final artifacts. Record their exact paths/hashes, validate agreement with stage 06, and bind requests to final bytes. Use `validated` only for an internally consistent draft without a legal-authority blocker; bounded factual limitations may yield a validated **partial draft**. Use `blocked` or `failed` when dependencies or integrity cannot support that result.
