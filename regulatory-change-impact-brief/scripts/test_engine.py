"""Synthetic contract tests. These fixtures are never production source evidence."""
import argparse
import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("engine", Path(__file__).with_name("engine.py"))
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
REPO = Path(__file__).resolve().parents[2]


def args(**values):
    return argparse.Namespace(**values)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="regulatory-contract-test-")
        self.root = Path(self.temp.name)
        shutil.copyfile(REPO / "snapshot.schema.json", self.root / "snapshot.schema.json")
        self.interview = self.root / "interviews/input.md"
        self.interview.parent.mkdir()
        self.interview.write_text("\n".join(f"[{label}](https://example.invalid/{label})" for label in engine.LABELS))
        self.run = engine.begin(self.root, args(interview="interviews/input.md", reason="Synthetic fixture run"))

    def tearDown(self):
        self.temp.cleanup()

    def table(self, label):
        headers = list(engine.TABLE_FIELDS[label])
        rows = {
            "SYSTEMS": [["SYS-1", "Example system", "Professional use", "Example owner", "no", "yes", "learners", "direct_interaction", "no", "human review", "complete", "2026-08-20", "revision-2026-08-26"]],
            "EVIDENCE": [["REC-1", "SYS-1", "incident", "2026-08-20", "Example owner", "open", "notice-ref", "complete", "notice absent"]],
            "CALENDAR": [["ACT-1", "SYS-1", "Verify notice", "Example owner", "2026-09-03", "open", "operations", "calendar-2026-08-26"]],
        }[label]
        return {"headers": headers, "rows": rows, "tab": "Native fixture tab", "range": "A1:Z25"}

    def capture(self, unavailable=None, malformed=None, calendar_due=None):
        sources = {}
        for label in engine.LABELS:
            raw = {"claim": f"Fresh fixture claim {label}"}
            version = {"version": "fixture-2026-08-26", "suitable_for_review": True}
            if label in engine.TABLE_FIELDS:
                version["normalized_table"] = self.table(label)
                if label == "CALENDAR" and calendar_due:
                    table = version["normalized_table"]
                    table["rows"][0][table["headers"].index("due_date")] = calendar_due
                    table["rows"][0][table["headers"].index("source_version")] = "calendar-2026-09-12"
                    table["headers"] = list(reversed(table["headers"])) + ["extra"]
                    table["rows"] = [list(reversed(table["rows"][0])) + ["legitimate new column"]]
                raw.update(version["normalized_table"])
            if label == malformed:
                version["normalized_table"]["headers"] = ["ambiguous"]
            raw_path = self.root / (label + ".json")
            engine.put(raw_path, raw)
            version_path = self.root / (label + "-version.json")
            engine.put(version_path, version)
            when = engine.now()
            source = engine.record(self.root, args(label=label, method="synthetic native test", url=self.run["routes"][label],
                                   status="unavailable" if label == unavailable else "retrieved", input=str(raw_path), version=str(version_path), error="synthetic failure" if label == unavailable else None,
                                   retrieved_at=when, request_started_at=when, content_type="application/json", source_role=None, authority=None))
            sources[label] = source
        return sources

    def analysis(self, sources, blocked=False):
        def record(rid, summary, eids, **extra):
            return {"id": rid, "summary": summary, "evidence_ids": eids, **extra}
        def citation(label):
            return [{"source_id": sources[label]["id"], "locator": "Fixture claim", "quote": f"Fresh fixture claim {label}"}]
        manifest_path = self.root / "deliverables/sources/manifest.json"
        analysis = {"run_id": self.run["run_id"], "manifest_sha256": engine.digest(manifest_path), "status": "blocked" if blocked else "partial",
                    "scope": {"systems_in_scope": ["SYS-1"], "audiences": ["Legal", "Operations"], "approval_gates": ["Human approval"], "review_type": "Synthetic contract test"},
                    "binding_rules": [record("RULE", "Generic rule extracted from a synthetic fixture", [sources["OJ"]["id"]], citations=citation("OJ"))],
                    "timing_rules": [], "guidance_context": [], "authority_blockers": [],
                    "system_facts": [record("FACT", "Captured fixture system use", [sources["SYSTEMS"]["id"]], system_id="SYS-1", citations=citation("SYSTEMS"))],
                    "policy_controls": [record("POLICY-CONTROL", "Captured fixture control", [sources["POLICY"]["id"]], citations=citation("POLICY"))],
                    "incident_evidence": [record("INCIDENT", "Captured fixture incident", [sources["EVIDENCE"]["id"]], system_id="SYS-1", citations=citation("EVIDENCE"))],
                    "conflicts": [], "evidence_gaps": [],
                    "impacts": [record("IMPACT", "Draft fixture impact", ["RULE", "FACT", "INCIDENT"], system_id="SYS-1", rule_ref="RULE", state="unresolved" if blocked else "supported-impact", reason="Fixture finding depends on captured rule and same-system facts.", owner="Example owner", proposed_action="ACT-1: Verify notice", proposed_due_date="2026-09-03", approval_status="pending")],
                    "unaffected_items": [], "unresolved_items": [],
                    "proposed_actions": [record("ACTION", "Verify notice", ["IMPACT", sources["CALENDAR"]["id"]], action_id="ACT-1", system_id="SYS-1", action="Verify notice", owner="Example owner", due_date="2026-09-03", status="open", approval_required="operations", source_version="calendar-2026-08-26", impact_ids=["IMPACT"], approval_status="pending", calendar_eligible=not blocked)],
                    "approval_requirements": [record("REQUEST", "Operations review", ["ACTION"], request_id="REQ-1", run_id=self.run["run_id"], source_versions={s["id"]: s["content_hash"] for s in sources.values() if s["retrieval_status"] == "retrieved"}, subject_system="SYS-1", subject_action="ACT-1", question="Confirm proposal?", required_reviewer="Operations", status="pending")],
                    "escalations": [], "decisions": [], "limitations": ["Synthetic fixture, never live source evidence."]}
        if blocked:
            analysis["authority_blockers"] = [record("BLOCKER", "Required synthetic binding source unavailable", [sources["AMEND"]["id"]], owner="Legal", resolution_need="Obtain required binding source before dependent interpretation.")]
        return analysis

    def publish(self, analysis):
        path = self.root / "analysis-input.json"
        engine.put(path, analysis)
        for seq in range(3, 7):
            engine.stage(self.root, args(sequence=seq, analysis=str(path)))
        return engine.build(self.root, args(analysis=str(path)))

    def test_complete_connected_draft_and_pending_calendar(self):
        analysis = self.analysis(self.capture())
        result = self.publish(analysis)
        self.assertTrue(result["validation"]["valid"], result)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(list((self.root / "deliverables/snapshots").glob("*.json"))), 7)
        self.assertIn(b"STATUS:TENTATIVE", (self.root / "deliverables/action-calendar.ics").read_bytes())

    def test_reordered_headers_rows_extra_columns_and_new_version(self):
        original = self.table("SYSTEMS")
        new = copy.deepcopy(original)
        new["headers"] = list(reversed(original["headers"])) + ["new_column"]
        new["rows"] = [list(reversed(original["rows"][0])) + ["new value"]]
        version_index = new["headers"].index("record_version")
        new["rows"][0][version_index] = "revision-2026-09-12"
        parsed = engine.parse_table("SYSTEMS", new)
        self.assertEqual(parsed[0]["system_id"], "SYS-1")
        self.assertEqual(parsed[0]["record_version"], "revision-2026-09-12")
        self.assertEqual(self.run["review_date"], "2026-08-26")

    def test_changed_calendar_rebuilds_all_drafts_without_changing_review_date(self):
        self.publish(self.analysis(self.capture()))
        self.run = engine.begin(self.root, args(interview="interviews/input.md", reason="Changed native calendar version"))
        analysis = self.analysis(self.capture(calendar_due="2026-09-10"))
        analysis["proposed_actions"][0]["due_date"] = "2026-09-10"
        analysis["proposed_actions"][0]["source_version"] = "calendar-2026-09-12"
        analysis["impacts"][0]["proposed_due_date"] = "2026-09-10"
        self.publish(analysis)
        for name in ("impact-register.csv", "compliance-brief.md"):
            self.assertIn("2026-09-10", (self.root / "deliverables" / name).read_text())
        self.assertIn(b"DTSTART;VALUE=DATE:20260910", (self.root / "deliverables/action-calendar.ics").read_bytes())
        self.assertEqual(engine.read(self.root / "deliverables/run.json")["review_date"], "2026-08-26")

    def test_cross_output_proposed_date_disagreement_rejected(self):
        analysis = self.analysis(self.capture())
        analysis["impacts"][0]["proposed_due_date"] = "2026-09-05"
        with self.assertRaises(engine.ReviewError):
            self.publish(analysis)

    def test_missing_ambiguous_headers_invalid_states_duplicate_ids(self):
        for mutation in ("missing", "duplicate_header", "invalid_value", "duplicate_id", "compact_date"):
            table = self.table("SYSTEMS")
            if mutation == "missing":
                table["headers"][0] = "unrecognized_alias"
            elif mutation == "duplicate_header":
                table["headers"][1] = table["headers"][0]
            elif mutation == "invalid_value":
                table["rows"][0][table["headers"].index("provider_role")] = "perhaps"
            elif mutation == "compact_date":
                table["rows"][0][table["headers"].index("evidence_updated_at")] = "20260904"
            else:
                table["rows"].append(list(table["rows"][0]))
            with self.subTest(mutation=mutation), self.assertRaises(engine.ReviewError):
                engine.parse_table("SYSTEMS", table)

    def test_malformed_attempt_is_preserved(self):
        sources = self.capture(malformed="SYSTEMS")
        source = sources["SYSTEMS"]
        self.assertTrue(source["table_validation_errors"])
        self.assertTrue(source["local_reference"])
        self.assertEqual(len(engine.read(self.root / "deliverables/sources/manifest.json")["sources"]), 10)

    def test_required_binding_unavailable_withholds_and_blocks(self):
        sources = self.capture(unavailable="AMEND")
        self.assertIsNone(sources["AMEND"]["content_hash"])
        self.assertIsNone(sources["AMEND"]["local_reference"])
        bad = self.analysis(sources)
        with self.assertRaises(engine.ReviewError):
            engine.check_analysis(self.root, self.run, engine.read(self.root / "deliverables/sources/manifest.json"), self.root / "deliverables/sources/manifest.json", bad)
        result = self.publish(self.analysis(sources, blocked=True))
        self.assertTrue(result["validation"]["valid"], result)
        self.assertEqual(result["publication_status"], "blocked")
        self.assertNotIn(b"BEGIN:VEVENT", (self.root / "deliverables/action-calendar.ics").read_bytes())

    def test_required_binding_label_cannot_be_disabled_by_authority_override(self):
        sources = self.capture(unavailable="AMEND")
        manifest_path = self.root / "deliverables/sources/manifest.json"
        manifest = engine.read(manifest_path)
        for source in manifest["sources"]:
            if source["label"] == "AMEND":
                source["authority"] = "advisory"
        engine.put(manifest_path, manifest)
        with self.assertRaisesRegex(engine.ReviewError, "Required binding authority unavailable/unsuitable.*AMEND"):
            engine.check_analysis(self.root, self.run, manifest, manifest_path, self.analysis(sources))

    def test_advisory_quote_cannot_become_an_operative_binding_rule(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        rule = analysis["binding_rules"][0]
        rule["evidence_ids"] = [sources["LAW"]["id"]]
        rule["citations"] = [{"source_id": sources["LAW"]["id"], "locator": "Fixture claim", "quote": "Fresh fixture claim LAW"}]
        manifest_path = self.root / "deliverables/sources/manifest.json"
        with self.assertRaisesRegex(engine.ReviewError, "Operative binding_rules record requires suitable original binding authority"):
            engine.check_analysis(self.root, self.run, engine.read(manifest_path), manifest_path, analysis)
        with self.assertRaisesRegex(engine.ReviewError, "Operative binding_rules"):
            self.publish(analysis)

    def test_documentary_consolidation_metadata_remains_nonoperative(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        documentary = {"id": "CONSOLIDATION-VERSION", "summary": "Documentary version, no legal effect.",
                       "evidence_ids": [sources["CONSOLIDATED"]["id"]], "authority": "documentary-no-legal-effect", "version": "fixture-2026-08-26",
                       "citations": [{"source_id": sources["CONSOLIDATED"]["id"], "locator": "Fixture claim", "quote": "Fresh fixture claim CONSOLIDATED"}]}
        analysis["timing_rules"] = [documentary]
        manifest_path = self.root / "deliverables/sources/manifest.json"
        documentary["application_date"] = "2026-09-03"
        with self.assertRaisesRegex(engine.ReviewError, "Operative timing_rules"):
            engine.check_analysis(self.root, self.run, engine.read(manifest_path), manifest_path, analysis)
        del documentary["application_date"]
        self.assertTrue(self.publish(analysis)["validation"]["valid"])

    def test_blocked_calendar_requires_explicit_nondependent_proposal(self):
        sources = self.capture(unavailable="AMEND")
        analysis = self.analysis(sources, blocked=True)
        action = analysis["proposed_actions"][0]
        action["calendar_eligible"] = True
        manifest_path = self.root / "deliverables/sources/manifest.json"
        for dependency in (None, True):
            if dependency is None:
                action.pop("legal_dependency", None)
            else:
                action["legal_dependency"] = dependency
            with self.subTest(dependency=dependency), self.assertRaisesRegex(engine.ReviewError, "forbids dependent dated calendar proposal"):
                engine.check_analysis(self.root, self.run, engine.read(manifest_path), manifest_path, analysis)
        action["legal_dependency"] = False
        result = self.publish(analysis)
        self.assertTrue(result["validation"]["valid"], result)
        self.assertEqual(result["publication_status"], "blocked")
        self.assertIn(b"BEGIN:VEVENT", (self.root / "deliverables/action-calendar.ics").read_bytes())

    def test_binding_impact_cannot_bypass_blocker_with_false_dependency_flag(self):
        sources = self.capture(unavailable="AMEND")
        analysis = self.analysis(sources, blocked=True)
        analysis["impacts"][0]["state"] = "supported-no-impact"
        analysis["impacts"][0]["legal_dependency"] = False
        manifest_path = self.root / "deliverables/sources/manifest.json"
        with self.assertRaisesRegex(engine.ReviewError, "Withhold dependent legal determination"):
            engine.check_analysis(self.root, self.run, engine.read(manifest_path), manifest_path, analysis)

    def test_invalid_source_classification_rejects_without_mutating_capture(self):
        self.capture()
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root / "deliverables").rglob("*") if p.is_file()}
        when = engine.now()
        for classification in ({"source_role": "internal-policy-and-context", "authority": None}, {"source_role": None, "authority": "internal-policy"}):
            with self.subTest(classification=classification), self.assertRaisesRegex(engine.ReviewError, "Unknown (source_role|authority)"):
                engine.record(self.root, args(label="POLICY", method="synthetic test", url=self.run["routes"]["POLICY"], status="retrieved", input=str(self.root / "POLICY.json"), version=str(self.root / "POLICY-version.json"), error=None,
                              retrieved_at=when, request_started_at=when, content_type="application/json", **classification))
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root / "deliverables").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_stale_analysis_and_old_retrieval_rejected(self):
        analysis = self.analysis(self.capture())
        analysis["manifest_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(engine.ReviewError):
            self.publish(analysis)
        with self.assertRaises(engine.ReviewError):
            engine.record(self.root, args(label="LAW", method="test", url=self.run["routes"]["LAW"], status="retrieved", input=str(self.root / "LAW.json"), version=None, error=None, retrieved_at="2020-01-01T00:00:00Z", request_started_at="2020-01-01T00:00:00Z", content_type="text/plain", source_role=None, authority=None))

    def test_capture_tamper_and_damaged_output_recovery_preserves_actual_history(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        self.publish(analysis)
        capture = self.root / sources["LAW"]["local_reference"]
        capture.write_text("damaged real fixture capture")
        self.assertFalse(engine.validate(self.root)["valid"])
        output = self.root / "deliverables/impact-register.csv"
        output.write_bytes(b"actual damaged bytes\n")
        old_id = self.run["run_id"]
        new = engine.begin(self.root, args(interview="interviews/input.md", reason="Recover actual damaged output"))
        archived = self.root / "deliverables/history" / old_id
        self.assertEqual((archived / "impact-register.csv").read_bytes(), b"actual damaged bytes\n")
        self.assertEqual((archived / "sources" / capture.name).read_text(), "damaged real fixture capture")
        self.assertEqual(new["supersedes_run_id"], old_id)
        self.assertNotEqual(new["run_id"], old_id)
        self.assertEqual(engine.read(self.root / "deliverables/sources/manifest.json")["sources"], [])
        history_check = engine.validate_history(self.root, old_id)
        self.assertTrue(history_check["archive_integrity_valid"])
        self.assertFalse(history_check["package_validation"]["valid"])
        self.assertFalse(history_check["pre_archive_validation"]["valid"])
        self.run = new
        result = self.publish(self.analysis(self.capture()))
        self.assertTrue(result["validation"]["valid"], result)
        self.assertTrue(archived.exists())

    def test_binding_subject_and_publication_artifact_tampering_rejected(self):
        self.publish(self.analysis(self.capture()))
        bindings_path = self.root / "deliverables/review-request-bindings.json"
        bindings = engine.read(bindings_path)
        bindings["requests"][0]["subject"] = {"subject_system": "OTHER"}
        engine.put(bindings_path, bindings)
        stage_path = self.root / "deliverables/snapshots/07-publication-validation.json"
        publication = engine.read(stage_path)
        for artifact in publication["state"]["artifacts"]:
            if artifact["path"].endswith("review-request-bindings.json"):
                artifact["sha256"] = engine.digest(bindings_path)
        engine.put(stage_path, publication)
        self.assertFalse(engine.validate(self.root)["valid"])
        publication["state"]["artifacts"] = []
        engine.put(stage_path, publication)
        result = engine.validate(self.root)
        self.assertTrue(any("required final artifact" in error for error in result["errors"]), result)

    def test_all_review_requests_have_independently_checked_hashes(self):
        analysis = self.analysis(self.capture())
        second = copy.deepcopy(analysis["approval_requirements"][0])
        second["id"], second["request_id"] = "REQUEST-2", "REQ-2"
        analysis["approval_requirements"].append(second)
        self.publish(analysis)
        bindings_path = self.root / "deliverables/review-request-bindings.json"
        bindings = engine.read(bindings_path)
        bindings["requests"][0]["drafts"][0]["sha256"] = "sha256:" + "0" * 64
        engine.put(bindings_path, bindings)
        publication_path = self.root / "deliverables/snapshots/07-publication-validation.json"
        publication = engine.read(publication_path)
        for artifact in publication["state"]["artifacts"]:
            if artifact["path"].endswith("review-request-bindings.json"):
                artifact["sha256"] = engine.digest(bindings_path)
        engine.put(publication_path, publication)
        result = engine.validate(self.root)
        self.assertTrue(any("bound hash no longer matches: REQ-1" in error for error in result["errors"]), result)

    def test_zero_review_requests_do_not_crash_valid_package(self):
        analysis = self.analysis(self.capture())
        analysis["approval_requirements"] = []
        result = self.publish(analysis)
        self.assertTrue(result["validation"]["valid"], result)

    def test_existing_archive_metadata_bytes_are_never_overwritten(self):
        self.publish(self.analysis(self.capture()))
        original = b'{"preserve":"actual original metadata bytes"}\n'
        (self.root / "deliverables/archive-manifest.json").write_bytes(original)
        old_id = self.run["run_id"]
        new = engine.begin(self.root, args(interview="interviews/input.md", reason="Restored run containing prior metadata"))
        archive = self.root / "deliverables/history" / old_id
        self.assertEqual((archive / "archive-manifest.json").read_bytes(), original)
        self.assertIn("archive-index-", new["supersedes_archive_metadata"])
        historical = engine.validate_history(self.root, old_id)
        self.assertTrue(historical["archive_integrity_valid"], historical)
        self.assertTrue(historical["package_validation"]["valid"], historical)

    def test_boundary_rejects_downstream_references_and_late_captures(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        analysis["binding_rules"][0]["evidence_ids"].append("IMPACT")
        path = self.root / "input.json"
        engine.put(path, analysis)
        with self.assertRaises(engine.ReviewError):
            engine.stage(self.root, args(sequence=3, analysis=str(path)))
        analysis["binding_rules"][0]["evidence_ids"].remove("IMPACT")
        engine.put(path, analysis)
        engine.stage(self.root, args(sequence=3, analysis=str(path)))
        when = engine.now()
        with self.assertRaises(engine.ReviewError):
            engine.record(self.root, args(label="LAW", method="test", url=self.run["routes"]["LAW"], status="retrieved", input=str(self.root / "LAW.json"), version=None, error=None, retrieved_at=when, request_started_at=when, content_type="text/plain", source_role=None, authority=None))

    def test_repeat_build_preserves_every_actual_file_byte(self):
        analysis = self.analysis(self.capture())
        self.publish(analysis)
        path = self.root / "analysis-input.json"
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root / "deliverables").rglob("*") if p.is_file()}
        with self.assertRaises(engine.MutationRejected):
            engine.build(self.root, args(analysis=str(path)))
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in (self.root / "deliverables").rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_first_publication_accepts_analysis_in_deliverables(self):
        analysis = self.analysis(self.capture())
        path = self.root / "deliverables/analysis.json"
        engine.put(path, analysis)
        for seq in range(3, 7):
            engine.stage(self.root, args(sequence=seq, analysis=str(path)))
        result = engine.build(self.root, args(analysis=str(path)))
        self.assertTrue(result["validation"]["valid"], result)
        self.assertEqual(engine.read(path), analysis)

    def test_partial_publication_is_retained_before_new_run(self):
        analysis = self.analysis(self.capture())
        path = self.root / "analysis-input.json"
        engine.put(path, analysis)
        partial = self.root / "deliverables/compliance-brief.md"
        partial.write_bytes(b"actual interrupted first draft bytes")
        run_before = (self.root / "deliverables/run.json").read_bytes()
        with self.assertRaises(engine.MutationRejected):
            engine.build(self.root, args(analysis=str(path)))
        self.assertEqual(partial.read_bytes(), b"actual interrupted first draft bytes")
        self.assertEqual((self.root / "deliverables/run.json").read_bytes(), run_before)
        old = self.run["run_id"]
        engine.begin(self.root, args(interview="interviews/input.md", reason="Recover interrupted first publication"))
        self.assertEqual((self.root / "deliverables/history" / old / "compliance-brief.md").read_bytes(), b"actual interrupted first draft bytes")

    def test_concurrent_capture_receipts_serialize_without_loss(self):
        self.capture()
        when = engine.now()
        def capture_once(_):
            return engine.record(self.root, args(label="LAW", method="concurrent synthetic test", url=self.run["routes"]["LAW"], status="retrieved", input=str(self.root / "LAW.json"), version=str(self.root / "LAW-version.json"), error=None, retrieved_at=when, request_started_at=when, content_type="application/json", source_role=None, authority=None))
        with ThreadPoolExecutor(max_workers=6) as pool:
            receipts = list(pool.map(capture_once, range(6)))
        manifest = engine.read(self.root / "deliverables/sources/manifest.json")
        self.assertEqual(len(manifest["sources"]), 16)
        self.assertEqual(len({s["id"] for s in receipts}), 6)
        self.assertEqual([s["id"] for s in manifest["sources"] if s["label"] == "LAW"], [f"SRC-LAW-{i:02}" for i in range(1, 8)])

    def test_brief_references_version_bindings_without_repeating_hashmaps(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        brief = engine.brief_bytes(self.run, engine.read(self.root / "deliverables/sources/manifest.json"), analysis).decode()
        self.assertIn("REQ-1", brief)
        self.assertIn("Confirm proposal?", brief)
        self.assertIn("review-request-bindings.json", brief)
        self.assertNotIn(sources["OJ"]["content_hash"], brief)

    def test_brief_groups_repeats_and_preserves_each_subject_and_action_mapping(self):
        sources = self.capture()
        analysis = self.analysis(sources)
        second_impact = copy.deepcopy(analysis["impacts"][0])
        second_impact.update(id="IMPACT-2", system_id="SYS-2", owner="Other owner", action_ids=["ACT-2"])
        analysis["impacts"].append(second_impact)
        second_action = copy.deepcopy(analysis["proposed_actions"][0])
        second_action.update(id="ACTION-2", action_id="ACT-2", system_id="SYS-2", impact_ids=["IMPACT-2"])
        analysis["proposed_actions"].append(second_action)
        second_request = copy.deepcopy(analysis["approval_requirements"][0])
        second_request.update(id="REQUEST-2", request_id="REQ-2", subject_system="SYS-2", subject_impact="IMPACT-2", subject_action="ACT-2")
        analysis["approval_requirements"].append(second_request)
        third_request = copy.deepcopy(second_request)
        third_request.update(id="REQUEST-3", request_id="REQ-3", question="Different question?")
        analysis["approval_requirements"].append(third_request)
        brief = engine.brief_bytes(self.run, engine.read(self.root / "deliverables/sources/manifest.json"), analysis).decode()
        self.assertEqual(brief.count(analysis["impacts"][0]["summary"]), 1)
        self.assertEqual(brief.count("Confirm proposal?"), 1)
        self.assertIn("IMPACT→SYS-1 (Example owner; ACT-1)", brief)
        self.assertIn("IMPACT-2→SYS-2 (Other owner; ACT-2)", brief)
        self.assertIn("REQ-1→SYS-1/ACT-1", brief)
        self.assertIn("REQ-2→SYS-2/IMPACT-2/ACT-2", brief)
        self.assertIn("REQ-3→SYS-2/IMPACT-2/ACT-2", brief)
        self.assertIn("Different question?", brief)

    def test_brief_identity_shared_limits_and_sentence_punctuation(self):
        sources = self.capture()
        manifest = engine.read(self.root / "deliverables/sources/manifest.json")
        for source in manifest["sources"]:
            if source["label"] == "POLICY":
                source["version_metadata"]["page_identity"] = "Native policy title"
            if source["label"] in ("LAW", "TIME", "FAQ"):
                source["version_metadata"]["authority_limit"] = "Shared advisory limitation."
        analysis = self.analysis(sources)
        analysis["guidance_context"] = [{"id": "GUIDE", "summary": "Sentence already ends in punctuation.", "evidence_ids": [sources["LAW"]["id"]]}]
        brief = engine.brief_bytes(self.run, manifest, analysis).decode()
        self.assertIn("Native policy title", brief)
        self.assertEqual(brief.count("Shared advisory limitation."), 1)
        self.assertIn("Sentence already ends in punctuation. Basis:", brief)
        self.assertNotIn("punctuation..", brief)

    def test_current_renderer_exact_bytes_and_legacy_layout_stored_hashes(self):
        self.publish(self.analysis(self.capture()))
        run_path = self.root / "deliverables/run.json"
        run = engine.read(run_path)
        self.assertEqual(run["renderer_version"], 3)
        brief_path = self.root / "deliverables/compliance-brief.md"
        brief_path.write_text(brief_path.read_text() + "\nLegacy layout annotation.\n")
        binding_path = self.root / "deliverables/review-request-bindings.json"
        bindings = engine.read(binding_path)
        for request in bindings["requests"]:
            for draft in request["drafts"]:
                if draft["path"].endswith("compliance-brief.md"):
                    draft["sha256"] = engine.digest(brief_path)
        engine.put(binding_path, bindings)
        publication_path = self.root / "deliverables/snapshots/07-publication-validation.json"
        publication = engine.read(publication_path)
        for artifact in publication["state"]["artifacts"]:
            artifact["sha256"] = engine.digest(self.root / artifact["path"])
        engine.put(publication_path, publication)
        self.assertFalse(engine.validate(self.root)["valid"])
        run["renderer_version"] = 2
        engine.put(run_path, run)
        self.assertTrue(engine.validate(self.root)["valid"])
        brief_path.write_text(brief_path.read_text() + "\nUnbound tampering.\n")
        self.assertFalse(engine.validate(self.root)["valid"])


if __name__ == "__main__":
    unittest.main()
