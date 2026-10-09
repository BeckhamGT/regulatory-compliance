#!/usr/bin/env python3
"""Validate and publish an agent's fresh, source-grounded review; never fetch sources.

Native app access belongs to the invoking agent. This helper deliberately has no
HTTP client, credentials, legal classifier, or canned business conclusions.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from functools import wraps
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import jsonschema
from icalendar import Calendar, Event

REVIEW_DATE = "2026-08-26"
AS_OF = "2026-08-26T23:59:59+01:00"
SCHEMA_VERSION = "regulatory-compliance-stage-snapshot/2"
LABELS = ("POLICY", "SYSTEMS", "EVIDENCE", "CALENDAR", "LAW", "OJ", "AMEND", "CONSOLIDATED", "TIME", "FAQ")
STAGES = ("scope", "source-capture", "authority-and-timing", "evidence-reconciliation", "impact-analysis", "actions-and-approvals", "publication-validation")
STAGE_KEYS = {3: ("binding_rules", "timing_rules", "guidance_context", "authority_blockers"),
              4: ("system_facts", "policy_controls", "incident_evidence", "conflicts", "evidence_gaps"),
              5: ("impacts", "unaffected_items", "conflicts", "unresolved_items"),
              6: ("proposed_actions", "approval_requirements", "escalations")}
CSV_FIELDS = ("impact_id", "system_id", "rule_ref", "state", "evidence_ids", "reason", "owner", "proposed_action", "proposed_due_date", "approval_status")
TABLE_FIELDS = {
    "SYSTEMS": ("system_id", "system_name", "use_case", "owner", "provider_role", "deployer_role", "exposed_group", "output_type", "current_notice", "human_review", "evidence_status", "evidence_updated_at", "record_version"),
    "EVIDENCE": ("record_id", "system_id", "record_type", "reported_at", "owner", "status", "evidence_ref", "evidence_state", "notes"),
    "CALENDAR": ("action_id", "system_id", "action", "owner", "due_date", "status", "approval_required", "source_version")}
TABLE_ENUMS = {
    "SYSTEMS": {"provider_role": {"yes", "no", "unknown"}, "deployer_role": {"yes", "no", "unknown"},
                "output_type": {"direct_interaction", "text", "synthetic_image", "classification", "synthetic_audio_video"},
                "current_notice": {"yes", "no", "unknown", "visible_label", "not_applicable"},
                "evidence_status": {"complete", "partial", "conflicting", "missing", "stale", "not_applicable"}},
    "EVIDENCE": {"record_type": {"evidence", "evidence_gap", "gap", "incident", "exception_request"}, "status": {"open", "closed", "draft", "blocked"},
                 "evidence_state": {"complete", "partial", "conflicting", "missing", "stale", "not_applicable"}},
    "CALENDAR": {"status": {"planned", "open", "blocked", "scheduled", "draft", "closed", "complete"}, "approval_required": {"legal", "operations", "both"}}}
SOURCE_ROLES = {"POLICY": ("internal-policy", "internal-control"), "SYSTEMS": ("operational-record", "operational-evidence"),
                "EVIDENCE": ("operational-record", "operational-evidence"), "CALENDAR": ("operational-record", "operational-evidence"),
                "OJ": ("binding-regulation", "binding"), "AMEND": ("binding-regulation", "binding"),
                "CONSOLIDATED": ("binding-regulation", "unknown"), "LAW": ("official-guidance", "advisory"),
                "TIME": ("official-guidance", "advisory"), "FAQ": ("official-guidance", "advisory")}
REQUIRED_BINDING_LABELS = frozenset(("OJ", "AMEND"))
SOURCE_ROLE_VALUES = frozenset(("binding-regulation", "official-guidance", "internal-policy", "operational-record", "other"))
AUTHORITY_VALUES = frozenset(("binding", "advisory", "internal-control", "operational-evidence", "unknown"))
STATUSES = {"complete", "partial", "blocked", "failed"}
RENDERER_VERSION = 3


class ReviewError(Exception):
    pass


class MutationRejected(ReviewError):
    """A closed boundary must be preserved, including its directory contents."""


def serialized(function):
    """Serialize all helper mutations across processes without repo lock files.

    flock releases automatically when a process exits, including interruption.
    The chosen runtime is POSIX Python (macOS/Linux); no stale-lock repair is
    necessary and concurrent capture receipts cannot lose manifest updates.
    """
    @wraps(function)
    def wrapped(root, *arguments, **keywords):
        key = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:24]
        lock_path = Path(tempfile.gettempdir()) / ("regulatory-impact-" + key + ".lock")
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                return function(root, *arguments, **keywords)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return wrapped


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def dt(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ReviewError(f"Timestamp needs timezone: {value}")
    return result


def canonical_date(value):
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ReviewError(f"Date must use YYYY-MM-DD: {value}")
    return date.fromisoformat(value)


def digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def root_path():
    completed = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True)
    return Path(completed.stdout.strip()).resolve()


def relative(root, path):
    return str(Path(path).resolve().relative_to(root.resolve()))


def inside(root, path):
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ReviewError(f"Path escapes repository: {path}")
    return result


def discover_routes(interview):
    matches = re.findall(r"\[([A-Z]+)\]\((https?://[^)\s]+)\)", Path(interview).read_text(encoding="utf-8"))
    routes = {}
    for label, url in matches:
        if label not in LABELS:
            continue
        if label in routes and routes[label] != url:
            raise ReviewError(f"Interview discloses conflicting {label} routes")
        routes[label] = url
    missing = set(LABELS) - set(routes)
    if missing:
        raise ReviewError(f"Interview lacks required routes: {sorted(missing)}")
    return routes


def parse_table(label, table):
    """Exact semantic headers; no positional assumptions or guessed aliases."""
    if label not in TABLE_FIELDS:
        raise ReviewError(f"No table contract for {label}")
    headers = [str(h).strip() for h in table["headers"]]
    if len(headers) != len(set(headers)):
        raise ReviewError(f"{label}: duplicate/ambiguous headers")
    missing = set(TABLE_FIELDS[label]) - set(headers)
    if missing:
        raise ReviewError(f"{label}: missing required headers {sorted(missing)}")
    records, seen = [], set()
    id_field = TABLE_FIELDS[label][0]
    for row_number, row in enumerate(table["rows"], 2):
        if not any(str(x).strip() for x in row):
            continue
        if len(row) > len(headers) and any(str(x).strip() for x in row[len(headers):]):
            raise ReviewError(f"{label} row {row_number}: values lack a header")
        record = {h: (str(row[i]).strip() if i < len(row) and row[i] is not None else "") for i, h in enumerate(headers)}
        record["_locator"] = f"{table.get('tab', 'unknown tab')}!row {row_number}"
        if not record[id_field] or record[id_field] in seen:
            raise ReviewError(f"{label}: missing or conflicting {id_field} at row {row_number}")
        seen.add(record[id_field])
        for name in ("due_date", "reported_at", "evidence_updated_at"):
            if name in record and record[name]:
                try:
                    canonical_date(record[name])
                except (ValueError, ReviewError):
                    raise ReviewError(f"{label}: invalid {name} at row {row_number}: {record[name]}")
        for field, allowed in TABLE_ENUMS[label].items():
            if record[field] not in allowed:
                raise ReviewError(f"{label}: invalid/unknown {field} at row {row_number}: {record[field]}")
        records.append(record)
    return records


def records_in(value):
    if isinstance(value, dict):
        if all(k in value for k in ("id", "summary", "evidence_ids")):
            yield value
        for child in value.values():
            yield from records_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from records_in(child)


def snapshot(root, run, seq, state, available, unresolved=(), decisions=(), status=None):
    path = root / "deliverables" / "snapshots" / f"{seq:02}-{STAGES[seq-1]}.json"
    previous = root / "deliverables" / "snapshots" / f"{seq-1:02}-{STAGES[seq-2]}.json" if seq > 1 else None
    stage_records = list(records_in(state)) + list(unresolved) + list(decisions)
    present = {r["id"] for r in stage_records}
    produced = sorted(present - available)
    consumed = sorted({eid for r in stage_records for eid in r.get("evidence_ids", []) if eid in available})
    if seq > 1 and not consumed:
        predecessor_ids = read(previous)["produced_record_ids"]
        consumed = predecessor_ids[:1] or sorted(available)[:1]
        state = dict(state)
        state["carry_forward_basis"] = {"id": f"BASIS-{seq:02}", "summary": "The predecessor's actual scope or unresolved state constrains this stage; no new supported determination is asserted by this carry-forward record.", "evidence_ids": consumed}
        present.add(f"BASIS-{seq:02}")
        produced = sorted(present - available)
    result = {"schema_version": SCHEMA_VERSION, "snapshot_id": f"{run['run_id']}:stage-{seq:02}",
              "run_id": run["run_id"], "stage": STAGES[seq-1], "sequence": seq,
              "created_at": now(), "status": status or run.get("status", "partial"),
              "predecessor": None if previous is None else {"snapshot_id": read(previous)["snapshot_id"], "path": relative(root, previous), "sha256": digest(previous)},
              "consumed_record_ids": consumed, "produced_record_ids": produced, "state": state,
              "unresolved": list(unresolved), "decisions": list(decisions)}
    put(path, result)
    return available | present


@serialized
def begin(root, args):
    interview = inside(root, args.interview)
    routes = discover_routes(interview)
    destination = root / "deliverables"
    old_id = None
    archive_metadata_reference = None
    recovery = []
    if destination.exists() and any(p.name != "history" for p in destination.iterdir()):
        prior_validation = validate(root)
        try:
            old_id = read(destination / "run.json")["run_id"]
        except (ValueError, OSError, KeyError):
            old_id = "unidentified-" + uuid.uuid4().hex[:12]
            recovery.append("Prior run metadata missing or damaged; actual files retained under an unidentified history ID.")
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", old_id)
        archive = destination / "history" / safe_id
        if archive.exists():
            raise MutationRejected(f"History already exists; refuse to overwrite {archive}")
        archive.mkdir(parents=True)
        for item in list(destination.iterdir()):
            if item.name != "history":
                shutil.move(str(item), str(archive / item.name))
        inventory = [{"logical_path": "deliverables/" + str(path.relative_to(archive)), "archived_path": relative(root, path), "sha256": digest(path)} for path in sorted(archive.rglob("*")) if path.is_file()]
        metadata_path = archive / "archive-manifest.json"
        while metadata_path.exists():
            metadata_path = archive / ("archive-index-" + uuid.uuid4().hex + ".json")
        archive_metadata_reference = relative(root, metadata_path)
        put(metadata_path, {"generated_by": "regulatory-change-impact-brief/1", "run_id": old_id, "archived_at": now(), "archive_reason": args.reason or "Fresh rerun", "original_logical_root": "deliverables/", "physical_root": relative(root, archive), "original_bytes_preserved": True, "pre_archive_validation": prior_validation, "inventory": inventory,
                                             "path_resolution": "Original snapshot/source/binding paths remain unchanged. Resolve each original deliverables/... path under this archive's physical_root; validate --history applies that mapping in an isolated temporary view."})
    started = now()
    run = {"run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12],
           "nonce": uuid.uuid4().hex, "created_at": started, "review_date": REVIEW_DATE, "as_of": AS_OF,
           "interview": relative(root, interview), "interview_sha256": digest(interview), "routes": routes,
           "schema_sha256": digest(root / "snapshot.schema.json"), "status": "partial", "supersedes_run_id": old_id,
           "supersedes_archive_metadata": archive_metadata_reference,
           "supersession_reason": args.reason or ("Fresh rerun; inspect all sources and outputs again." if old_id else "Initial run"),
           "recovery_notes": recovery}
    put(destination / "run.json", run)
    put(destination / "sources" / "manifest.json", {"run_id": run["run_id"], "nonce": run["nonce"], "sources": []})
    scope = {"as_of": AS_OF, "review_type": "Draft Article 50 change-impact review", "systems_in_scope": ["Registered EU programme uses (live register identity pending)"],
             "audiences": ["Legal", "Operations"], "approval_gates": ["Legal interpretation and exceptions", "Operations activation, dates and closure"],
             "supersedes_run_id": old_id, "supersession_reason": run["supersession_reason"],
             "scope_record": {"id": "SCOPE", "summary": "Review intent is fixed to 26 August 2026; operational facts require fresh source retrieval.", "evidence_ids": [], "interview_sha256": run["interview_sha256"]}}
    snapshot(root, run, 1, scope, set())
    return run


def current(root):
    run = read(root / "deliverables" / "run.json")
    manifest_path = root / "deliverables" / "sources" / "manifest.json"
    manifest = read(manifest_path)
    if manifest["run_id"] != run["run_id"] or manifest["nonce"] != run["nonce"]:
        raise ReviewError("Manifest belongs to another run")
    if run["review_date"] != REVIEW_DATE or run["as_of"] != AS_OF:
        raise ReviewError("Assigned review date changed")
    if digest(root / "snapshot.schema.json") != run["schema_sha256"]:
        raise ReviewError("Public schema changed during run")
    if digest(inside(root, run["interview"])) != run["interview_sha256"]:
        raise ReviewError("Original interview changed during run")
    return run, manifest, manifest_path


@serialized
def record(root, args):
    run, manifest, manifest_path = current(root)
    if (root / "deliverables/snapshots/03-authority-and-timing.json").exists():
        raise MutationRejected("Source-capture boundary is closed; begin a new run before another attempt")
    label = args.label.upper()
    if label not in run["routes"] or args.url != run["routes"][label]:
        raise ReviewError("Source route must exactly match this run's original interview")
    if args.source_role is not None and args.source_role not in SOURCE_ROLE_VALUES:
        raise ReviewError(f"Unknown source_role: {args.source_role}")
    if args.authority is not None and args.authority not in AUTHORITY_VALUES:
        raise ReviewError(f"Unknown authority: {args.authority}")
    ordinal = sum(s["label"] == label for s in manifest["sources"]) + 1
    source_id = f"SRC-{label}-{ordinal:02}"
    retrieved_at = args.retrieved_at or now()
    request_started_at = args.request_started_at or retrieved_at
    if dt(request_started_at) < dt(run["created_at"]) or dt(retrieved_at) < dt(request_started_at):
        raise ReviewError("Capture predates run or has invalid retrieval chronology")
    if dt(retrieved_at) > datetime.now(timezone.utc) + timedelta(minutes=1):
        raise ReviewError("Retrieval timestamp is in the future")
    if args.status == "retrieved" and not (args.input and args.retrieved_at and args.request_started_at):
        raise ReviewError("Fresh retrieval requires content and actual request/retrieval timestamps")
    version = read(args.version) if args.version else None
    defaults = SOURCE_ROLES[label]
    source = {"id": source_id, "summary": f"{label} attempt {ordinal} via {args.method}: {args.status}", "evidence_ids": [],
              "label": label, "method": args.method, "source_role": args.source_role or defaults[0], "authority": args.authority or defaults[1],
              "locator": args.url, "request_started_at": request_started_at, "retrieved_at": retrieved_at,
              "ingested_at": now(), "retrieval_status": args.status, "content_type": args.content_type or "text/plain",
              "version_metadata": version, "content_hash": None, "local_reference": None,
              "run_id": run["run_id"], "nonce": run["nonce"], "error": args.error or None,
              "time_basis": "actual-tool-attempt" if args.request_started_at and args.retrieved_at else "ingestion-only"}
    if args.status in ("retrieved", "unverified", "stale") and args.input:
        payload = Path(args.input).read_bytes()
        if not payload.strip():
            raise ReviewError("Empty content is not a source capture")
        suffix = Path(args.input).suffix or ".txt"
        target = root / "deliverables" / "sources" / (source_id + suffix)
        target.write_bytes(payload)
        source["local_reference"], source["content_hash"] = relative(root, target), digest(target)
    elif args.input or args.error:
        diagnostic = root / "deliverables" / "sources" / (source_id + ".diagnostic.txt")
        diagnostic.write_bytes(Path(args.input).read_bytes() if args.input else args.error.encode("utf-8"))
        source["diagnostic_reference"], source["diagnostic_hash"] = relative(root, diagnostic), digest(diagnostic)
    if version and "normalized_table" in version:
        try:
            source["normalized_records"] = parse_table(label, version["normalized_table"])
            if source.get("local_reference"):
                captured_text = source_text(root, source)
                for item in source["normalized_records"]:
                    for key, value in item.items():
                        if key != "_locator" and value and value not in captured_text:
                            raise ReviewError(f"Normalized {label} value is absent from raw source capture: {key}={value}")
        except (ReviewError, KeyError, TypeError) as exc:
            source.pop("normalized_records", None)
            source["table_validation_errors"] = [str(exc)]
            source["summary"] += "; table is unsuitable until its recorded validation errors are resolved"
    manifest["sources"].append(source)
    put(manifest_path, manifest)
    snapshot(root, run, 2, {"sources": manifest["sources"], "manifest_sha256": digest(manifest_path)}, {"SCOPE"})
    return source


def source_text(root, source):
    raw = inside(root, source["local_reference"]).read_text(encoding="utf-8")
    try:
        return raw + "\n" + json.dumps(json.loads(raw), ensure_ascii=False) + "\n" + flatten_text(json.loads(raw))
    except ValueError:
        return raw


def flatten_text(value):
    if isinstance(value, dict):
        return "\n".join(flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return "\n".join(flatten_text(v) for v in value)
    return str(value)


def suitable_binding_source(source, run):
    """Caller metadata cannot turn another route into required legal authority."""
    return bool(source and source.get("label") in REQUIRED_BINDING_LABELS and
                source.get("locator") == run["routes"].get(source["label"]) and
                source.get("retrieval_status") == "retrieved" and
                source.get("authority") == "binding" and source.get("local_reference") and
                (source.get("version_metadata") or {}).get("suitable_for_review") is True)


def operative_authority_errors(analysis, sources, run):
    errors = []
    for key in ("binding_rules", "timing_rules"):
        for item in analysis.get(key, []):
            cited = [sources.get(c.get("source_id")) for c in item.get("citations", [])]
            # A dated consolidation's disclaimer/version is documentary metadata,
            # not a commencement or application rule. Preserve that legitimate
            # explicit classification in actual prior runs as well as new runs.
            documentary = (key == "timing_rules" and item.get("authority") == "documentary-no-legal-effect" and
                           cited and all(s and s.get("label") == "CONSOLIDATED" and
                                         s.get("retrieval_status") == "retrieved" for s in cited) and
                           not any(item.get(k) for k in ("application_date", "effective_date", "entry_into_force", "market_entry_cutoff")))
            if not documentary and not any(suitable_binding_source(s, run) for s in cited):
                errors.append(f"Operative {key} record requires suitable original binding authority: {item['id']}")
    return errors


def check_analysis(root, run, manifest, manifest_path, analysis):
    errors = []
    if analysis.get("run_id") != run["run_id"] or analysis.get("manifest_sha256") != digest(manifest_path):
        errors.append("Analysis is stale or belongs to a different capture manifest")
    if analysis.get("status") not in STATUSES:
        errors.append("Analysis requires explicit complete/partial/blocked/failed status")
    sources = {s["id"]: s for s in manifest["sources"]}
    attempted = {s["label"] for s in sources.values()}
    if attempted != set(LABELS):
        errors.append(f"Every run requires all ten fresh route attempts; missing {sorted(set(LABELS)-attempted)}")
    blocked = []
    for label in sorted(REQUIRED_BINDING_LABELS):
        suitable = [s for s in sources.values() if s["label"] == label and suitable_binding_source(s, run)]
        if not suitable:
            blocked.append(label)
    if blocked and analysis.get("status") != "blocked":
        errors.append(f"Required binding authority unavailable/unsuitable: {blocked}; run must be blocked")
    if blocked and not analysis.get("authority_blockers"):
        errors.append("Blocked authority requires explicit source-backed authority_blockers")
    all_records = list(records_in(analysis))
    record_ids = {r["id"] for r in all_records}
    allowed_ids = record_ids | set(sources) | {"SCOPE"}
    by_id = {}
    for record_item in all_records:
        record_id = record_item["id"]
        if record_id in by_id and by_id[record_id] != record_item:
            errors.append(f"Conflicting record ID: {record_id}")
        by_id[record_id] = record_item
        if not record_item.get("summary"):
            errors.append(f"Empty summary: {record_id}")
        for eid in record_item.get("evidence_ids", []):
            if eid not in allowed_ids:
                errors.append(f"Unknown evidence ID {eid} in {record_id}")
        for citation in record_item.get("citations", []):
            source = sources.get(citation.get("source_id"))
            if not source or source["retrieval_status"] != "retrieved" or not source.get("local_reference"):
                errors.append(f"Citation lacks freshly retrieved source: {record_id}")
                continue
            if not citation.get("locator") or not citation.get("quote"):
                errors.append(f"Citation needs source locator and exact quote: {record_id}")
            elif citation["quote"] not in source_text(root, source):
                errors.append(f"Citation quote absent from capture: {record_id} / {source['id']}")
            if source["id"] not in record_item.get("evidence_ids", []):
                errors.append(f"Citation source missing from evidence_ids: {record_id}")
    for key in ("binding_rules", "timing_rules", "system_facts", "policy_controls", "incident_evidence"):
        for record_item in analysis.get(key, []):
            if not record_item.get("citations"):
                errors.append(f"Source-derived {key} record requires an exact captured citation: {record_item['id']}")
    errors.extend(operative_authority_errors(analysis, sources, run))
    system_sources = [s for s in sources.values() if s["label"] == "SYSTEMS" and s["retrieval_status"] == "retrieved" and s.get("normalized_records")]
    system_ids = {r["system_id"] for r in system_sources[-1]["normalized_records"]} if system_sources else set()
    if not system_ids and analysis.get("status") == "complete":
        errors.append("Complete review requires a usable native system register")
    for source in sources.values():
        if source.get("table_validation_errors") and analysis.get("status") == "complete":
            errors.append(f"Complete review uses malformed native table: {source['id']}")
        for item in source.get("normalized_records", []):
            if source["label"] in ("EVIDENCE", "CALENDAR") and system_ids and item["system_id"] not in system_ids | {"ALL"}:
                errors.append(f"Orphan system ID in {source['label']}: {item['system_id']}")
    legal_rule_ids = {r["id"] for r in analysis.get("binding_rules", [])}
    rules = legal_rule_ids | {r["id"] for r in analysis.get("policy_controls", [])}
    def dependencies(record_id, visited=None):
        visited = set() if visited is None else visited
        if record_id in visited:
            return visited
        visited.add(record_id)
        for eid in by_id.get(record_id, {}).get("evidence_ids", []):
            dependencies(eid, visited)
        return visited
    pairs, covered_systems = set(), set()
    for impact in analysis.get("impacts", []):
        if not impact.get("evidence_ids") or not impact.get("reason") or not impact.get("system_id") or not impact.get("rule_ref"):
            errors.append(f"Incomplete reasoned impact: {impact['id']}")
        if impact.get("approval_status", "pending") != "pending":
            errors.append(f"Draft impact approval must stay pending: {impact['id']}")
        pair = (impact.get("system_id"), impact.get("rule_ref"))
        if pair in pairs:
            errors.append(f"Duplicate system/rule impact row: {pair}")
        pairs.add(pair)
        covered_systems.add(impact.get("system_id"))
        if system_ids and impact.get("system_id") not in system_ids:
            errors.append(f"Impact refers to unregistered system: {impact['id']}")
        if impact.get("rule_ref") not in rules:
            errors.append(f"Impact rule_ref is not an actual binding-rule or policy-control record: {impact['id']}")
        reachable = dependencies(impact["id"])
        if impact.get("rule_ref") not in reachable:
            errors.append(f"Impact evidence chain does not consume its claimed rule: {impact['id']}")
        facts = [r for r in analysis.get("system_facts", []) + analysis.get("incident_evidence", []) if r.get("system_id") == impact.get("system_id")]
        if facts and not any(r["id"] in reachable for r in facts):
            errors.append(f"Impact omits captured same-system factual basis: {impact['id']}")
        if impact.get("state") in ("supported-impact", "supported-no-impact") and not any(r["id"] in reachable for r in facts):
            errors.append(f"Supported determination lacks source-grounded system facts: {impact['id']}")
        if blocked and impact.get("state") in ("supported-impact", "supported-no-impact") and (impact.get("legal_dependency", True) or impact.get("rule_ref") in legal_rule_ids):
            errors.append(f"Withhold dependent legal determination while authority is blocked: {impact['id']}")
        if impact.get("proposed_due_date"):
            canonical_date(impact["proposed_due_date"])
    covered_systems.update(r.get("system_id") for r in analysis.get("unaffected_items", []))
    if system_ids - covered_systems:
        errors.append(f"Scoped systems missing from impact/unaffected results: {sorted(system_ids-covered_systems)}")
    actions = analysis.get("proposed_actions", [])
    action_ids = set()
    for action in actions:
        aid = action.get("action_id", action["id"])
        if aid in action_ids:
            errors.append(f"Duplicate action ID: {aid}")
        action_ids.add(aid)
        if action.get("approval_status", "pending") != "pending":
            errors.append(f"Proposed action approval must stay pending: {aid}")
        if not action.get("system_id") or not action.get("action", action.get("summary")):
            errors.append(f"Action lacks system or description: {aid}")
        if system_ids and action.get("system_id") not in system_ids | {"ALL"}:
            errors.append(f"Action refers to unregistered system: {aid}")
        for iid in action.get("impact_ids", []):
            if iid not in {i["id"] for i in analysis.get("impacts", [])}:
                errors.append(f"Action refers to missing impact: {aid} / {iid}")
        if action.get("due_date"):
            canonical_date(action["due_date"])
            if blocked and action.get("calendar_eligible", True) and action.get("legal_dependency") is not False:
                errors.append(f"Blocked legal authority forbids dependent dated calendar proposal: {aid}; omit it or explicitly establish a nondependent basis")
        if not action.get("evidence_ids"):
            errors.append(f"Action lacks source or decision basis: {aid}")
    amap = {a.get("action_id", a["id"]): a for a in actions}
    for impact in analysis.get("impacts", []):
        linked_ids = set(impact.get("action_ids", [])) | {aid for aid, action in amap.items() if impact["id"] in action.get("impact_ids", [])}
        if linked_ids - set(amap):
            errors.append(f"Impact links nonexistent actions: {impact['id']} / {sorted(linked_ids-set(amap))}")
        linked = [amap[aid] for aid in linked_ids if aid in amap]
        if impact.get("proposed_action") and not linked:
            errors.append(f"Impact proposal lacks a linked stage06 action: {impact['id']}")
        if any(a["system_id"] not in {impact["system_id"], "ALL"} for a in linked):
            errors.append(f"Impact links an action for another system: {impact['id']}")
        if impact.get("proposed_due_date") and impact["proposed_due_date"] not in {a.get("due_date") for a in linked}:
            errors.append(f"Impact proposed date contradicts its linked calendar actions: {impact['id']}")
    for request in analysis.get("approval_requirements", []):
        for field in ("request_id", "run_id", "source_versions", "question", "required_reviewer"):
            if not request.get(field):
                errors.append(f"Review request lacks {field}: {request['id']}")
        if request.get("run_id") != run["run_id"] or request.get("status") != "pending":
            errors.append(f"Review request must match run and remain pending: {request['id']}")
        if not any(request.get(k) for k in ("subject_system", "subject_impact", "subject_action", "subject")):
            errors.append(f"Review request lacks subject: {request['id']}")
        if not request.get("evidence_ids"):
            errors.append(f"Review request lacks evidence: {request['id']}")
        versions = request.get("source_versions")
        if not isinstance(versions, dict) or not versions:
            errors.append(f"Review request source_versions must map source IDs to capture hashes: {request['id']}")
        else:
            for sid, version_hash in versions.items():
                if sid not in sources or sources[sid]["retrieval_status"] != "retrieved" or sources[sid]["content_hash"] != version_hash:
                    errors.append(f"Review request names unavailable/stale source version: {request['id']} / {sid}")
            required_versions = {sid for sid in dependencies(request["id"]) if sid in sources and sources[sid]["retrieval_status"] == "retrieved"}
            if required_versions - set(versions):
                errors.append(f"Review request omits versions from its evidence chain: {request['id']} / {sorted(required_versions-set(versions))}")
        for field, subject_ids in (("subject_system", system_ids | {"ALL"}), ("subject_impact", {i["id"] for i in analysis.get("impacts", [])}), ("subject_action", action_ids)):
            if request.get(field) and request[field] not in subject_ids:
                errors.append(f"Review request has unknown {field}: {request['id']}")
    for key in ("unresolved_items", "evidence_gaps", "escalations", "authority_blockers"):
        for issue in analysis.get(key, []):
            if not issue.get("owner") or not (issue.get("resolution_need") or issue.get("question")):
                errors.append(f"Unresolved item needs named owner and resolution need: {issue['id']}")
    # Preserve all native calendar commitments; retaining a date is not approval.
    calendars = [s for s in sources.values() if s["label"] == "CALENDAR" and s["retrieval_status"] == "retrieved" and s.get("normalized_records")]
    if calendars:
        latest = calendars[-1]
        amap = {a.get("action_id", a["id"]): a for a in actions}
        for item in latest["normalized_records"]:
            aid = item["action_id"]
            if aid not in amap:
                errors.append(f"Existing calendar commitment omitted: {aid}")
            elif amap[aid].get("due_date", "") != item["due_date"]:
                errors.append(f"Existing calendar date changed without authorized decision: {aid}")
    if errors:
        raise ReviewError("\n".join(errors))
    return blocked


def csv_bytes(analysis):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for impact in analysis.get("impacts", []):
        writer.writerow({"impact_id": impact["id"], "system_id": impact.get("system_id", ""), "rule_ref": impact.get("rule_ref", ""),
                         "state": impact["state"], "evidence_ids": ";".join(impact["evidence_ids"]), "reason": impact["reason"],
                         "owner": impact.get("owner") or "", "proposed_action": impact.get("proposed_action") or "",
                         "proposed_due_date": impact.get("proposed_due_date") or "", "approval_status": impact.get("approval_status", "pending")})
    return stream.getvalue().encode("utf-8")


def calendar_bytes(run, analysis):
    calendar = Calendar()
    calendar.add("prodid", "-//Regulatory Change Impact Brief//Draft review//EN")
    calendar.add("version", "2.0")
    for action in analysis.get("proposed_actions", []):
        if not action.get("due_date") or action.get("calendar_eligible", True) is False:
            continue
        event = Event()
        action_id = action.get("action_id", action["id"])
        event.add("uid", f"{action_id}@regulatory-change-impact-brief")
        event.add("dtstamp", dt(run["created_at"]))
        event.add("dtstart", date.fromisoformat(action["due_date"]))
        event.add("dtend", date.fromisoformat(action["due_date"]) + timedelta(days=1))
        event.add("summary", f"DRAFT {action_id}: {action.get('action', action['summary'])}")
        event.add("description", f"Run: {run['run_id']}\nAction: {action_id}\nSystem: {action['system_id']}\nOwner/role: {action.get('owner') or 'pending Operations'}\nRequired reviewer: {action.get('approval_required') or 'Legal/Operations pending'}\nEvidence/source-decision basis: {';'.join(action['evidence_ids'])}\nSource version: {action.get('source_version') or 'see source manifest'}\nApproval: pending; dates remain proposals.\nSource status: {action.get('status', 'draft')}")
        event.add("status", "TENTATIVE")
        calendar.add_component(event)
    return calendar.to_ical()


def md_escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def md_row(values):
    return "|" + "|".join(md_escape(value) for value in values) + "|"


def sentence(value):
    text = str(value).strip()
    return text if not text or text.endswith((".", "?", "!")) else text + "."


def brief_bytes(run, manifest, analysis):
    lines = ["# Regulatory change impact brief", "", f"Run: `{run['run_id']}` · Review date: **{REVIEW_DATE}** · Status: **{analysis['status']}**",
             "", "**Draft for Legal and Operations. Interpretation, exceptions, activation, dates and closure require human decisions. Requests remain pending and unsent.**",
             "", "Full reasoning: `impact-register.csv` and snapshots 03–06. Every capture/version: `sources/manifest.json`. Exact final-draft bindings: `review-request-bindings.json`. Retrieval times do not change the review date.", "", "## Source access and version limits", "",
             "| Route / attempts | Source identity and version | Latest retrieval | Suitability / historical limit |", "|---|---|---|---|"]
    limit_counts = {}
    for label in LABELS:
        attempts = [s for s in manifest["sources"] if s["label"] == label]
        successful = [s for s in attempts if s["retrieval_status"] == "retrieved"]
        version = (max(successful or attempts, key=lambda s: s["retrieved_at"]).get("version_metadata") or {})
        for key in ("authority_limit", "historical_limit", "review_suitability"):
            if version.get(key):
                value = str(version[key])
                limit_counts[value] = limit_counts.get(value, 0) + 1
    shared_limits = {text: f"L{n}" for n, text in enumerate((text for text, count in limit_counts.items() if count > 1), 1)}
    for label in LABELS:
        attempts = [s for s in manifest["sources"] if s["label"] == label]
        successful = [s for s in attempts if s['retrieval_status'] == 'retrieved']
        source = max(successful or attempts, key=lambda s: s['retrieved_at'])
        version = source.get("version_metadata") or {}
        version_labels = [str(version[k]) for k in ("version", "version_date", "policy_version", "context_revision", "context_observation_date", "context_authored_date", "last_update", "publication_date", "effective_date") if version.get(k)]
        row_versions = {r.get("record_version") or r.get("source_version") for r in source.get("normalized_records", [])} - {None, ""}
        version_labels.extend(sorted(row_versions))
        identity = str(version.get("identity") or version.get("title") or version.get("page_identity") or "Identity not established")
        identity_version = identity + ("; " + "; ".join(version_labels) if version_labels else "; version not established")
        limits = [shared_limits.get(str(version[k]), str(version[k])) for k in ("authority_limit", "historical_limit", "review_suitability") if version.get(k)]
        if not limits:
            limits = ["Suitable captured version" if version.get("suitable_for_review") is True else "Historical suitability not established"]
        failures = [s for s in attempts if s.get("error")]
        limits.extend(f"{s['id']}: {s['error']}" for s in failures)
        values = (f"[{label}]({source['locator']}): " + "; ".join(f"{s['id']} {s['retrieval_status']}" for s in attempts), identity_version, max(s["retrieved_at"] for s in attempts), " ".join(limits))
        lines.append(md_row(values))
    if shared_limits:
        lines += [""] + [f"- **{label}:** {text}" for text, label in shared_limits.items()]
    lines += ["", "## Authority and timing basis", ""]
    for key in ("binding_rules", "timing_rules", "guidance_context"):
        for item in analysis.get(key, []):
            lines.append(f"- `{item['id']}` {sentence(item['summary'])} Basis: {', '.join('`'+e+'`' for e in item['evidence_ids'])}.")
    lines += ["", "Exact quotations and company facts: snapshots 03–04. Evidence states do not establish compliance."]
    impacts = analysis.get("impacts", [])
    counts = {state: sum(i["state"] == state for i in impacts) for state in ("supported-impact", "supported-no-impact", "conflicting", "unresolved")}
    lines += ["", "## Findings", "", "; ".join(f"{count} {state}" for state, count in counts.items()) + ". Details: `impact-register.csv`.", "",
              "Grouped mappings share the stated rule, state and finding. Supported-no-impact proposals apply only to the cited use and rule.", "",
              "| Rule / state | Finding | Impact → system / owner / actions |", "|---|---|---|"]
    groups = {}
    for impact in impacts:
        groups.setdefault((impact["rule_ref"], impact["state"], impact["summary"]), []).append(impact)
    for (rule, state, summary), findings in groups.items():
        mappings = []
        for impact in findings:
            action_ids = impact.get("action_ids", []) or [a.get("action_id", a["id"]) for a in analysis.get("proposed_actions", []) if impact["id"] in a.get("impact_ids", [])]
            mappings.append(f"{impact['id']}→{impact['system_id']} ({impact.get('owner') or 'unassigned'}; {','.join(action_ids) or 'none'})")
        lines.append(md_row((f"{rule} / {state}", summary, "; ".join(mappings))))
    for item in analysis.get("unaffected_items", []):
        lines.append(f"- `{item['id']}` {item['summary']} (basis: {', '.join(item['evidence_ids'])}).")
    lines += ["", "## Conflicts and unresolved matters", "", "The named resolver must settle each issue; resolution questions and evidence are in snapshots 03–06.", "",
              "| Issue | Retained uncertainty / conflict | Resolver | Basis |", "|---|---|---|---|"]
    seen = set()
    for key in ("authority_blockers", "conflicts", "evidence_gaps", "unresolved_items", "escalations"):
        for item in analysis.get(key, []):
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            lines.append(md_row((item["id"], item["summary"], item.get("owner") or "unassigned", ",".join(item["evidence_ids"]))))
    lines += ["", "## Proposed actions and calendar", "", "All proposals remain **pending**; source status grants no approval or closure. Omitted actions have no event.", "",
              "| Action / system | Proposal | Owner / proposed date | Source status / reviewer | Basis |", "|---|---|---|---|---|"]
    for action in analysis.get("proposed_actions", []):
        aid = action.get("action_id", action["id"])
        due = action.get("due_date") or "undated; omitted pending Operations"
        omitted = "; omitted: " + action.get("calendar_omission_reason", "unsupported date or blocked dependency") if action.get("due_date") and action.get("calendar_eligible", True) is False else ""
        values = (f"{aid} / {action['system_id']}", action.get("action", action["summary"]), f"{action.get('owner') or 'unassigned'} / {due}{omitted}", f"{action.get('status', 'draft')} / {action.get('approval_required') or 'pending'}", ",".join(action["evidence_ids"]))
        lines.append(md_row(values))
    lines += ["", "## Legal and Operations review requests", ""]
    lines += ["Requests remain **pending and unsent**, bound to this run, captured versions and final drafts in `review-request-bindings.json`. Snapshot 06 retains full evidence. Identical questions share a row.", "",
              "| Required reviewer / question | Request → subjects |", "|---|---|"]
    request_groups = {}
    for request in analysis.get("approval_requirements", []):
        request_groups.setdefault((request["required_reviewer"], request["question"]), []).append(request)
    for (reviewer, question), requests in request_groups.items():
        subjects = []
        for request in requests:
            subject = "/".join(str(request[k]) for k in ("subject", "subject_system", "subject_impact", "subject_action") if request.get(k))
            subjects.append(f"{request['request_id']}→{subject}")
        lines.append(md_row((f"{reviewer}: {question}", "; ".join(subjects))))
    lines += ["", "## Limitations", ""]
    lines.extend("- " + limitation for limitation in analysis.get("limitations", []))
    lines += ["", "## Recorded workflow decisions", "", "Full concerns, options, rationale and tradeoffs remain in snapshots 03–06.", "",
              "| Decision | Recorded concern | Basis |", "|---|---|---|"]
    for decision in analysis.get("decisions", []):
        lines.append(md_row((decision["id"], decision["summary"], ",".join(decision["evidence_ids"]))))
    return ("\n".join(lines) + "\n").encode("utf-8")


@serialized
def stage(root, args):
    """Persist a real stage boundary before the invoking agent proceeds."""
    run, manifest, manifest_path = current(root)
    analysis = read(args.analysis)
    if analysis.get("run_id") != run["run_id"] or analysis.get("manifest_sha256") != digest(manifest_path):
        raise ReviewError("Stage input is stale or belongs to another run")
    if analysis.get("status") not in STATUSES:
        raise ReviewError("Stage input requires an honest run status")
    seq = args.sequence
    target = root / "deliverables/snapshots" / f"{seq:02}-{STAGES[seq-1]}.json"
    if target.exists():
        raise MutationRejected("Stage boundary already exists; preserve it and begin a new run to change its basis")
    available = set()
    for prior in range(1, seq):
        prior_path = root / "deliverables/snapshots" / f"{prior:02}-{STAGES[prior-1]}.json"
        available.update(read(prior_path)["produced_record_ids"])
    state = {key: analysis.get(key, []) for key in STAGE_KEYS[seq]}
    records = list(records_in(state))
    local_ids = {r["id"] for r in records}
    sources = {s["id"]: s for s in manifest["sources"]}
    if {s["label"] for s in manifest["sources"]} != set(LABELS):
        raise ReviewError("All ten source routes must be attempted before authority reconciliation")
    for item in records:
        if not set(item["evidence_ids"]).issubset(available | local_ids):
            raise ReviewError(f"Stage {seq} references evidence unavailable at this boundary: {item['id']}")
        for citation in item.get("citations", []):
            source = sources.get(citation.get("source_id"))
            if not source or source["retrieval_status"] != "retrieved" or not citation.get("quote") or citation["quote"] not in source_text(root, source) or not citation.get("locator") or source["id"] not in item["evidence_ids"]:
                raise ReviewError(f"Stage {seq} citation is not backed by this capture: {item['id']}")
    for key in set(STAGE_KEYS[seq]) & {"binding_rules", "timing_rules", "system_facts", "policy_controls", "incident_evidence"}:
        for item in state[key]:
            if not item.get("citations"):
                raise ReviewError(f"Source-derived record needs exact citation at boundary: {item['id']}")
    if seq == 3:
        authority_errors = operative_authority_errors(state, sources, run)
        if authority_errors:
            raise ReviewError("\n".join(authority_errors))
    unresolved = state.get("authority_blockers", []) + state.get("evidence_gaps", []) + state.get("unresolved_items", []) + state.get("escalations", [])
    decisions = [d for d in analysis.get("decisions", []) if d.get("stage", 6) == seq]
    snapshot(root, run, seq, state, available, unresolved, decisions, analysis["status"])
    put(root / "deliverables/stage-inputs" / f"{seq:02}.json", analysis)
    return {"run_id": run["run_id"], "sequence": seq, "snapshot": relative(root, target), "sha256": digest(target)}


@serialized
def build(root, args):
    run, manifest, manifest_path = current(root)
    publication_paths = ("publication-attempt.json", "impact-register.csv", "compliance-brief.md", "action-calendar.ics", "review-request-bindings.json", "snapshots/07-publication-validation.json")
    existing = [name for name in publication_paths if (root / "deliverables" / name).exists()]
    if existing:
        raise MutationRejected(f"Publication already started ({', '.join(existing)}); preserve this actual package and begin a new run before rebuilding")
    analysis = read(args.analysis)
    blocked = check_analysis(root, run, manifest, manifest_path, analysis)
    available = set()
    for seq in range(1, 7):
        boundary = root / "deliverables/snapshots" / f"{seq:02}-{STAGES[seq-1]}.json"
        if not boundary.exists():
            raise ReviewError(f"Stage {seq} boundary absent: call stage before downstream reasoning/publication")
        prior_snapshot = read(boundary)
        if seq in STAGE_KEYS:
            expected_state = {key: analysis.get(key, []) for key in STAGE_KEYS[seq]}
            actual_state = {key: prior_snapshot["state"][key] for key in STAGE_KEYS[seq]}
            if actual_state != expected_state:
                raise ReviewError(f"Final analysis changed stage {seq} after its boundary; begin a new run")
        available.update(prior_snapshot["produced_record_ids"])
    destination = root / "deliverables"
    drafts = {"impact-register.csv": csv_bytes(analysis), "compliance-brief.md": brief_bytes(run, manifest, analysis), "action-calendar.ics": calendar_bytes(run, analysis)}
    put(destination / "publication-attempt.json", {"run_id": run["run_id"], "started_at": now(), "analysis_sha256": digest(args.analysis), "status": "rendering", "recovery_owner": "Workflow operator", "on_failure": "Preserve all actual files and begin a new run before retrying"})
    run["status"] = analysis["status"]
    run["renderer_version"] = RENDERER_VERSION
    put(destination / "run.json", run)
    put(destination / "analysis.json", analysis)
    for name, payload in drafts.items():
        (destination / name).write_bytes(payload)
    draft_bindings = [{"path": relative(root, destination / name), "sha256": digest(destination / name)} for name in drafts]
    bindings = {"run_id": run["run_id"], "manifest_sha256": digest(manifest_path), "created_at": now(), "status": "draft-unsent", "requests": []}
    for request in analysis.get("approval_requirements", []):
        bindings["requests"].append({"request_id": request["request_id"], "record_id": request["id"], "run_id": run["run_id"],
                                     "subject": {k: request[k] for k in ("subject", "subject_system", "subject_impact", "subject_action") if k in request},
                                     "required_reviewer": request["required_reviewer"], "source_versions": request["source_versions"],
                                     "evidence_ids": request["evidence_ids"], "question": request["question"], "status": "pending", "delivery_status": "unsent",
                                     "drafts": draft_bindings})
    put(destination / "review-request-bindings.json", bindings)
    artifact_evidence = {"impact-register.csv": [i["id"] for i in analysis.get("impacts", [])], "compliance-brief.md": sorted(available),
                         "action-calendar.ics": [a["id"] for a in analysis.get("proposed_actions", [])],
                         "review-request-bindings.json": [r["id"] for r in analysis.get("approval_requirements", [])] + ["ART-" + name.split(".")[0] for name in drafts]}
    artifacts = [{"id": "ART-" + name.split(".")[0], "summary": f"Final draft artifact {name}, bound to the actual consumed review records.",
                  "evidence_ids": artifact_evidence[name], "path": relative(root, destination / name), "sha256": digest(destination / name), "validation_status": "valid"} for name in (*drafts, "review-request-bindings.json")]
    checks = [{"id": "CHECK-DRAFT", "summary": "Final draft bytes written; schema, evidence, predecessor and output agreement checked against actual files by validate.", "evidence_ids": sorted(available) + [a["id"] for a in artifacts], "result": "pending-full-validation"}]
    publication = "blocked" if analysis["status"] == "blocked" or blocked else "failed" if analysis["status"] == "failed" else "validated"
    snapshot(root, run, 7, {"artifacts": artifacts, "validation_checks": checks, "publication_status": publication,
                           "approval_status": "pending", "binding_path": "deliverables/review-request-bindings.json"}, available)
    result = validate(root)
    if not result["valid"]:
        put(destination / "validation-report.json", result)
        raise ReviewError("Rendered package failed validation: " + "; ".join(result["errors"]))
    stage7 = read(destination / "snapshots" / "07-publication-validation.json")
    stage7["state"]["validation_checks"][0]["result"] = "pass"
    stage7["state"]["validation_checks"][0]["checked_at"] = now()
    put(destination / "snapshots" / "07-publication-validation.json", stage7)
    result = validate(root)
    put(destination / "validation-report.json", result)
    put(destination / "publication-attempt.json", {"run_id": run["run_id"], "started_at": read(destination / "publication-attempt.json")["started_at"], "finished_at": now(), "analysis_sha256": digest(args.analysis), "status": "validated" if result["valid"] else "failed", "publication_status": publication, "recovery_owner": "Workflow operator"})
    return {"run_id": run["run_id"], "status": run["status"], "publication_status": publication, "validation": result}


def brief_semantic_errors(payload, run, analysis):
    """Inspect old layouts without regenerating or silently rewriting history."""
    text = payload.decode("utf-8")
    required = [run["run_id"], REVIEW_DATE, analysis["status"], "pending", "Legal", "Operations", "review-request-bindings.json"]
    for item in analysis.get("impacts", []):
        required.extend((item["id"], item["system_id"], item["state"]))
    for action in analysis.get("proposed_actions", []):
        required.extend((action.get("action_id", action["id"]), action["system_id"], action.get("action", action["summary"])))
        if action.get("due_date"):
            required.append(action["due_date"])
    for request in analysis.get("approval_requirements", []):
        required.extend((request["request_id"], request["required_reviewer"], request["question"]))
    required.extend(analysis.get("limitations", []))
    return [f"Brief omits required review value: {value}" for value in required if value not in text]


def validate(root):
    errors, checks = [], []
    try:
        run, manifest, manifest_path = current(root)
        analysis = read(root / "deliverables" / "analysis.json")
        check_analysis(root, run, manifest, manifest_path, analysis)
        if analysis["status"] != run["status"]:
            errors.append("Bound analysis and run status disagree")
        schema = jsonschema.Draft202012Validator(read(root / "snapshot.schema.json"), format_checker=jsonschema.FormatChecker())
        available, seen_records = set(), {}
        for seq in range(1, 8):
            path = root / "deliverables" / "snapshots" / f"{seq:02}-{STAGES[seq-1]}.json"
            obj = read(path)
            errors.extend(f"stage {seq} schema: {error.message}" for error in schema.iter_errors(obj))
            if obj["sequence"] != seq or obj["stage"] != STAGES[seq-1] or obj["run_id"] != run["run_id"]:
                errors.append(f"Stage {seq} run/sequence disagreement")
            if seq == 1:
                if obj["state"]["as_of"] != AS_OF:
                    errors.append("Review date drift")
            else:
                previous = root / "deliverables" / "snapshots" / f"{seq-1:02}-{STAGES[seq-2]}.json"
                expected = {"snapshot_id": read(previous)["snapshot_id"], "path": relative(root, previous), "sha256": digest(previous)}
                if obj["predecessor"] != expected:
                    errors.append(f"Stage {seq} predecessor hash/identity mismatch")
            if not set(obj["consumed_record_ids"]).issubset(available):
                errors.append(f"Stage {seq} consumes unavailable upstream records")
            local_records = list(records_in(obj["state"])) + obj["unresolved"] + obj["decisions"]
            present = {r["id"] for r in local_records}
            if not set(obj["produced_record_ids"]).issubset(present):
                errors.append(f"Stage {seq} produced IDs absent from its actual state")
            if set(obj["produced_record_ids"]) != present - available:
                errors.append(f"Stage {seq} produced record provenance mismatch")
            for record_item in local_records:
                if not set(record_item["evidence_ids"]).issubset(available | present):
                    errors.append(f"Stage {seq} unknown evidence reference in {record_item['id']}")
                rid = record_item["id"]
                if rid in seen_records and record_item != seen_records[rid]:
                    errors.append(f"Record changed without new identity across stages: {rid}")
                seen_records[rid] = record_item
            available |= present
            checks.append(f"stage-{seq:02}: schema and chain checked")
        source_index = {s["id"]: s for s in manifest["sources"]}
        for source in source_index.values():
            if source.get("local_reference"):
                if digest(inside(root, source["local_reference"])) != source["content_hash"]:
                    errors.append(f"Capture hash mismatch: {source['id']}")
            elif source["content_hash"] is not None:
                errors.append(f"Hash without requested source content: {source['id']}")
            if source["retrieval_status"] in ("unavailable", "invalid") and (source["local_reference"] is not None or source["content_hash"] is not None):
                errors.append(f"Failed retrieval used as requested content: {source['id']}")
            if source.get("diagnostic_reference") and digest(inside(root, source["diagnostic_reference"])) != source["diagnostic_hash"]:
                errors.append(f"Diagnostic hash mismatch: {source['id']}")
            if source["run_id"] != run["run_id"] or source["nonce"] != run["nonce"] or dt(source["request_started_at"]) < dt(run["created_at"]):
                errors.append(f"Capture does not belong to this fresh run: {source['id']}")
            if source.get("normalized_records"):
                try:
                    reparsed = parse_table(source["label"], source["version_metadata"]["normalized_table"])
                    if reparsed != source["normalized_records"]:
                        errors.append(f"Normalized table records disagree with raw table version: {source['id']}")
                except (ReviewError, KeyError, TypeError) as exc:
                    errors.append(f"Current table contract check failed for {source['id']}: {exc}")
        if read(root / "deliverables/snapshots/02-source-capture.json")["state"]["sources"] != manifest["sources"]:
            errors.append("Stage02 source records differ from capture manifest")
        for seq, keys in STAGE_KEYS.items():
            stage_obj = read(root / "deliverables/snapshots" / f"{seq:02}-{STAGES[seq-1]}.json")
            state = stage_obj["state"]
            for key in keys:
                if state[key] != analysis.get(key, []):
                    errors.append(f"Stage{seq:02} {key} differs from bound analysis")
            if stage_obj["decisions"] != [d for d in analysis.get("decisions", []) if d.get("stage", 6) == seq]:
                errors.append(f"Stage{seq:02} decisions differ from bound analysis")
        expected_drafts = {"impact-register.csv": csv_bytes(analysis), "compliance-brief.md": brief_bytes(run, manifest, analysis), "action-calendar.ics": calendar_bytes(run, analysis)}
        for name, payload in expected_drafts.items():
            actual = (root / "deliverables" / name).read_bytes()
            if name == "compliance-brief.md" and run.get("renderer_version") != RENDERER_VERSION:
                errors.extend(brief_semantic_errors(actual, run, analysis))
            elif actual != payload:
                errors.append(f"Final {name} disagrees with bound stage06/analysis")
        calendar = Calendar.from_ical((root / "deliverables/action-calendar.ics").read_bytes())
        if str(calendar.get("VERSION")) != "2.0" or not calendar.get("PRODID"):
            errors.append("Calendar lacks RFC5545 VERSION/PRODID")
        actions = {a.get("action_id", a["id"]): a for a in analysis.get("proposed_actions", []) if a.get("due_date") and a.get("calendar_eligible", True)}
        events = calendar.walk("VEVENT")
        if len(events) != len(actions):
            errors.append("Calendar event/action count mismatch")
        seen_uids = set()
        for event in events:
            uid = str(event.get("UID"))
            if uid in seen_uids:
                errors.append("Duplicate calendar UID")
            seen_uids.add(uid)
            aid = uid.split("@")[0]
            action = actions.get(aid)
            if not action or str(event.get("STATUS")) != "TENTATIVE" or not event.get("DTSTAMP"):
                errors.append(f"Invalid pending calendar action: {uid}")
                continue
            start, end = event.decoded("DTSTART"), event.decoded("DTEND")
            if isinstance(start, datetime) or start != date.fromisoformat(action["due_date"]) or end != start + timedelta(days=1):
                errors.append(f"All-day calendar date/exclusive end mismatch: {aid}")
            description = str(event.get("DESCRIPTION"))
            if not all(value in description for value in (aid, action["system_id"], "pending", *action["evidence_ids"])):
                errors.append(f"Calendar description omits review basis: {aid}")
        bindings = read(root / "deliverables/review-request-bindings.json")
        requests = {r["request_id"]: r for r in analysis.get("approval_requirements", [])}
        if bindings["run_id"] != run["run_id"] or bindings.get("manifest_sha256") != digest(manifest_path) or len(bindings["requests"]) != len(requests):
            errors.append("Review binding run/request count mismatch")
        for binding in bindings["requests"]:
            request = requests.get(binding["request_id"])
            expected_subject = {k: request[k] for k in ("subject", "subject_system", "subject_impact", "subject_action") if k in request} if request else {}
            if not request or binding["run_id"] != run["run_id"] or binding["record_id"] != request["id"] or binding["subject"] != expected_subject or binding["question"] != request["question"] or binding["required_reviewer"] != request["required_reviewer"] or binding["source_versions"] != request["source_versions"] or binding["evidence_ids"] != request["evidence_ids"] or binding["status"] != "pending" or binding["delivery_status"] != "unsent":
                errors.append(f"Review request binding mismatch: {binding['request_id']}")
            expected_paths = {"deliverables/" + n for n in expected_drafts}
            if {d["path"] for d in binding["drafts"]} != expected_paths:
                errors.append(f"Review request missing final draft binding: {binding['request_id']}")
            for draft in binding["drafts"]:
                if digest(inside(root, draft["path"])) != draft["sha256"]:
                    errors.append(f"Review request bound hash no longer matches: {binding['request_id']}")
        stage7 = read(root / "deliverables/snapshots/07-publication-validation.json")["state"]
        if read(root / "deliverables/snapshots/07-publication-validation.json")["status"] != run["status"]:
            errors.append("Final snapshot/run status disagreement")
        required_artifacts = {"deliverables/" + name for name in (*expected_drafts, "review-request-bindings.json")}
        if {a["path"] for a in stage7["artifacts"]} != required_artifacts or len(stage7["artifacts"]) != len(required_artifacts):
            errors.append("Publication does not bind the exact required final artifact set")
        for artifact in stage7["artifacts"]:
            if not artifact.get("summary") or "evidence_ids" not in artifact:
                errors.append(f"Publication artifact lacks produced-record provenance: {artifact['id']}")
            if digest(inside(root, artifact["path"])) != artifact["sha256"] or artifact["validation_status"] != "valid":
                errors.append(f"Publication artifact mismatch: {artifact['id']}")
        expected_publication = "blocked" if run["status"] == "blocked" else "failed" if run["status"] == "failed" else "validated"
        if stage7["publication_status"] != expected_publication:
            errors.append("Publication status disagrees with current run limitations")
        checks += ["ten fresh source routes and capture hashes checked", "exact captured citations checked", "CSV/brief/calendar agree with bound analysis", "RFC5545 pending events checked", "detached review-request hashes checked"]
    except (ReviewError, OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return {"valid": not errors, "checked_at": now(), "errors": errors, "checks": checks, "approval_status": "pending"}


def validate_history(root, run_id):
    """Resolve retained logical paths without rewriting any historical bytes."""
    archive = inside(root, "deliverables/history/" + run_id)
    candidates = [archive / "archive-manifest.json", *archive.glob("archive-index-*.json")]
    manifests = []
    for candidate in candidates:
        try:
            data = read(candidate)
            if data.get("physical_root") == relative(root, archive) and data.get("run_id") == run_id and "inventory" in data:
                manifests.append((data["archived_at"], candidate.name, data))
        except (ValueError, OSError, KeyError, TypeError):
            continue
    if not manifests:
        raise ReviewError(f"No archive metadata resolves retained run {run_id}")
    archive_manifest = sorted(manifests, key=lambda entry: (entry[0], entry[1]))[-1][2]
    inventory_errors = []
    for item in archive_manifest["inventory"]:
        if digest(inside(root, item["archived_path"])) != item["sha256"]:
            inventory_errors.append(f"Archived bytes changed: {item['archived_path']}")
    with tempfile.TemporaryDirectory(prefix="regulatory-history-check-") as directory:
        view = Path(directory)
        shutil.copytree(archive, view / "deliverables")
        shutil.copyfile(root / "snapshot.schema.json", view / "snapshot.schema.json")
        historical_run = read(archive / "run.json")
        interview_source = inside(root, historical_run["interview"])
        interview_target = inside(view, historical_run["interview"])
        interview_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(interview_source, interview_target)
        package = validate(view)
    return {"run_id": run_id, "archive_integrity_valid": not inventory_errors, "archive_integrity_errors": inventory_errors,
            "package_validation": package, "pre_archive_validation": archive_manifest["pre_archive_validation"], "original_bytes_preserved": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("begin")
    p.add_argument("--interview", required=True)
    p.add_argument("--reason")
    p = sub.add_parser("record")
    p.add_argument("--label", required=True, choices=LABELS)
    p.add_argument("--method", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--status", required=True, choices=("retrieved", "unavailable", "invalid", "unverified", "stale"))
    for name in ("input", "version", "error", "retrieved-at", "request-started-at", "content-type", "source-role", "authority"):
        p.add_argument("--" + name)
    p = sub.add_parser("build")
    p.add_argument("--analysis", required=True)
    p = sub.add_parser("stage")
    p.add_argument("--sequence", required=True, type=int, choices=(3, 4, 5, 6))
    p.add_argument("--analysis", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--json", action="store_true")
    p.add_argument("--history", help="Read-only validation of one archived run using its original logical paths")
    args = parser.parse_args()
    root = root_path()
    try:
        result = {"begin": begin, "record": record, "stage": stage, "build": build}.get(args.command, lambda r, a: validate_history(r, a.history) if a.history else validate(r))(root, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == "validate" and args.history:
            return 0 if result["archive_integrity_valid"] and result["package_validation"]["valid"] else 1
        if args.command == "validate" and not result["valid"]:
            failure = {"failed_at": now(), "command": "validate", "affected_stage": "publication-validation", "affected_output": "actual current package", "error": result["errors"], "recovery_owner": "Workflow operator", "required_recovery": "Preserve damaged output, begin a new run, retrieve all ten routes freshly, then rebuild."}
            put(root / "deliverables/failures" / (uuid.uuid4().hex[:12] + ".json"), failure)
            return 1
        return 0
    except (ReviewError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        failure = {"failed_at": now(), "command": args.command, "error": str(exc), "recovery_owner": "Workflow operator", "required_recovery": "Preserve current files, repair the cause, begin a new run, retrieve all ten routes freshly, then rebuild."}
        destination = root / "deliverables" / "failures"
        if (root / "deliverables/run.json").exists() and not isinstance(exc, MutationRejected):
            put(destination / (uuid.uuid4().hex[:12] + ".json"), failure)
        print(json.dumps(failure, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
