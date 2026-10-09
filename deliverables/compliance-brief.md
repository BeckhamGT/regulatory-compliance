# Regulatory change impact brief

Run: `20261009T023909Z-2f738d94e1e1` · Review date: **2026-08-26** · Status: **blocked**

**Draft for Legal and Operations. Interpretation, exceptions, activation, dates and closure require human decisions. Requests remain pending and unsent.**

Full reasoning: `impact-register.csv` and snapshots 03–06. Every capture/version: `sources/manifest.json`. Exact final-draft bindings: `review-request-bindings.json`. Retrieval times do not change the review date.

## Source access and version limits

| Route / attempts | Source identity and version | Latest retrieval | Suitability / historical limit |
|---|---|---|---|
|[POLICY](https://private-pecorino-70e.notion.site/Project-2-Regulatory-Compliance-Current-Internal-Policies-3ba0b700541e81f09998d48f3b1c2856): SRC-POLICY-01 unavailable; SRC-POLICY-02 unavailable; SRC-POLICY-03 retrieved|Browser tab: 7, Title: "Project 2 Regulatory Compliance — Current Internal Policies", URL: "https://private-pecorino-70e.notion.site/Project-2-Regulatory-Compliance-Current-Internal-Policies-3ba0b700541e81f09998d48f3b1c2856".; AI-POL-2026-08-15; RC-CONTEXT-2026-09-12-R1; 2026-08-26|2026-10-09T02:39:56.738Z|L1 SRC-POLICY-01: Native Notion object_not_found 404; requested policy page not obtained. SRC-POLICY-02: Native Notion object_not_found 404; requested policy page not obtained.|
|[SYSTEMS](https://docs.google.com/spreadsheets/d/10ky745H_1h9XbGCXPJsiRp5yfdeU08TZtmrsCMinGgU): SRC-SYSTEMS-01 retrieved|Project B — AI System Register; register-2026-08-26|2026-10-09T02:39:43.965Z|L2|
|[EVIDENCE](https://docs.google.com/spreadsheets/d/19BYZ68OSbsa1i9OfF6MzthrdC6q6mt6IWk6ucI8u7Rk): SRC-EVIDENCE-01 retrieved|Project B — Incident and Evidence Register; version not established|2026-10-09T02:39:44.380Z|L2|
|[CALENDAR](https://docs.google.com/spreadsheets/d/1xtXl_P7Yb9LaECZjjgtlyI-idoAJTAhH-1gQ4vQaCGA): SRC-CALENDAR-01 retrieved|Project B — Compliance Calendar; calendar-2026-08-26|2026-10-09T02:39:43.930Z|L2|
|[LAW](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50): SRC-LAW-01 unavailable; SRC-LAW-02 retrieved|Browser tab: 7, Title: "Article 50: Transparency obligations for providers and deployers of certain AI systems \| AI Act Service Desk", URL: "https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50".; version not established|2026-10-09T02:42:51.597Z|L1 SRC-LAW-01: HTTP 429 Too Many Requests; requested page not obtained through reader.|
|[OJ](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng): SRC-OJ-01 unavailable; SRC-OJ-02 unavailable|Identity not established; version not established|2026-10-09T02:40:11.578Z|Historical suitability not established SRC-OJ-01: Initial navigation observation was incomplete and contained no requested document text; unused. Later fresh navigation/readiness observations retained separately. SRC-OJ-02: Original EUR-Lex request redirected to TodayOJ current journal listing during a displayed service outage; requested document identity, version and claim-bearing text were absent.|
|[AMEND](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ%3AL_202601744): SRC-AMEND-01 unavailable; SRC-AMEND-02 unavailable|Identity not established; version not established|2026-10-09T02:41:19.556Z|Historical suitability not established SRC-AMEND-01: Initial navigation observation was incomplete and contained no requested document text; unused. Later fresh navigation/readiness observations retained separately. SRC-AMEND-02: Original EUR-Lex request redirected to TodayOJ current journal listing during a displayed service outage; requested document identity, version and claim-bearing text were absent.|
|[CONSOLIDATED](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02024R1689-20260727): SRC-CONSOLIDATED-01 unavailable; SRC-CONSOLIDATED-02 unavailable|Identity not established; version not established|2026-10-09T02:39:55.291Z|Historical suitability not established SRC-CONSOLIDATED-01: Initial navigation observation was incomplete and contained no requested document text; unused. Later fresh navigation/readiness observations retained separately. SRC-CONSOLIDATED-02: Original EUR-Lex request redirected to TodayOJ current journal listing during a displayed service outage; requested document identity, version and claim-bearing text were absent.|
|[TIME](https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline): SRC-TIME-01 retrieved|Timeline for the Implementation of the EU AI Act \| AI Act Service Desk (https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline); version not established|2026-10-09T02:39:17.998Z|L3|
|[FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act): SRC-FAQ-01 retrieved|Transparency obligations under Article 50 of the AI Act \| Shaping Europe’s digital future (https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act); version not established|2026-10-09T02:39:18.524Z|L3|

- **L1:** Native page last-edited time and revision history are unavailable; live current text does not independently prove exact August 26 page state.
- **L2:** Live workbook modified after August 26; dated row labels are reported versions. Native revision list returned no revisions, so the exact historical workbook cannot be verified.
- **L3:** Live current guidance; no retrievable historical page revision proving exact August 26 wording. Legislative reconciliation remains withheld while original binding routes are unavailable.

## Authority and timing basis

- `GUIDE-LAW` Fresh Service Desk page says its displayed text uses the July 27 consolidation and marks amendments. It reproduces Article 50 paragraph text, including AMENDED paragraph 7; the summary panel was collapsed and was not used. This route is retained as advisory/context rather than a substitute for the original acts. The original act, amendment operations and dated consolidation cannot be compared in this run. Basis: `SRC-LAW-02`.
- `GUIDE-FAQ-CONFLICT` The current FAQ overview names paragraph 50(2) for direct interaction, while its later interaction answer names 50(1). Preserve both advisory references; no binding paragraph choice is confirmed in this run. Basis: `SRC-FAQ-01`.
- `GUIDE-TIME` The undated current timeline describes an August 2 transparency milestone and a limited December 2 provider marking transition. These are advisory site claims, not verified operative timing or an internal-policy postponement. Basis: `SRC-TIME-01`.
- `GUIDE-FAQ-DATE` FAQ displays July 24, 2026 as its update date. A current retrieval and displayed date cannot establish its exact August 26 historical page state. Basis: `SRC-FAQ-01`.

Exact quotations and company facts: snapshots 03–04. Evidence states do not establish compliance.

## Findings

2 supported-impact; 1 supported-no-impact; 2 conflicting; 11 unresolved. Details: `impact-register.csv`.

Grouped mappings share the stated rule, state and finding. Supported-no-impact proposals apply only to the cited use and rule.

| Rule / state | Finding | Impact → system / owner / actions |
|---|---|---|
|POL-AUTHORITY / unresolved|Statutory applicability, actor duties, exceptions and timing are withheld because required original legislation and amendment were not retrieved. POL-AUTHORITY identifies the internal human-review gate, not a reconstructed statutory paragraph. This row does not assess or certify any Article 50 paragraph.|IMP-AI-001-AUTHORITY→AI-001 (Learner Operations; PROP-RESTORE-AUTHORITY); IMP-AI-002-AUTHORITY→AI-002 (Admissions; PROP-RESTORE-AUTHORITY); IMP-AI-003-AUTHORITY→AI-003 (Communications; PROP-RESTORE-AUTHORITY); IMP-AI-004-AUTHORITY→AI-004 (Learning Experience; PROP-RESTORE-AUTHORITY); IMP-AI-005-AUTHORITY→AI-005 (Assessment Operations; PROP-RESTORE-AUTHORITY); IMP-AI-006-AUTHORITY→AI-006 (People Operations; PROP-RESTORE-AUTHORITY); IMP-AI-007-AUTHORITY→AI-007 (Marketing; PROP-RESTORE-AUTHORITY); IMP-AI-008-AUTHORITY→AI-008 (Communications; PROP-RESTORE-AUTHORITY)|
|POL-NOTICE / supported-no-impact|Register reports a notice and REC-001 reports agreement between screenshot and release. No extra internal-policy notice remediation is supported on these reports; actual proof and accessibility remain unverified. This is not a statutory no-impact finding.|IMP-AI-001-NOTICE→AI-001 (Learner Operations; none)|
|POL-DRAFT / unresolved|Owner reports private staff drafts and individually edited emails, while REC-002 lacks recipient disclosure evidence. Confirm the actual output flow under internal policy without inferring a statutory breach or exemption.|IMP-AI-002-DRAFT→AI-002 (Admissions; ACT-003)|
|POL-SYNTHETIC / conflicting|Register complete/visible-label status and REC-003 possible metadata loss conflict. August policy supports checking final published-copy provenance; the fictional image description does not resolve that evidence.|IMP-AI-003-SYNTHETIC→AI-003 (Communications; ACT-004)|
|POL-NOTICE / supported-impact|Register and REC-004 report direct spoken interaction without first-interaction notice. Internal policy supports proposed notice remediation; no contextual exception is evidenced. Operations activation and incident closure remain pending.|IMP-AI-004-NOTICE→AI-004 (Learning Experience; ACT-001)|
|POL-EVIDENCE / supported-impact|Stale current-role evidence and missing technical/release facts support an internal-policy evidence refresh. Human adjudication does not settle biometric functionality or provider facts; statutory applicability stays withheld.|IMP-AI-005-EVIDENCE→AI-005 (Assessment Operations; ACT-005)|
|POL-NOTICE / conflicting|Register/capture says no notice while the owner reports a banner. A fictional graphic alone does not establish that visitors understand the conversation. Verify first-interaction evidence and retain both reports.|IMP-AI-007-NOTICE→AI-007 (Marketing; ACT-002)|
|POL-SYNTHETIC / unresolved|Visible label is reported, but surviving machine-readable provenance and tool support are untested. Proposed testing follows August policy and does not decide any statutory grace period.|IMP-AI-008-SYNTHETIC→AI-008 (Communications; ACT-006)|
|POL-EXCEPTION / unresolved|REC-010 has no recorded Legal approval or expiry. Review may gather the missing exception facts; the generated request grants no exception and cannot waive policy.|IMP-AI-008-EXCEPTION→AI-008 (Communications; ACT-007)|

## Conflicts and unresolved matters

The named resolver must settle each issue; resolution questions and evidence are in snapshots 03–06.

| Issue | Retained uncertainty / conflict | Resolver | Basis |
|---|---|---|---|
|BLOCK-OJ|Original Regulation 2024/1689 route redirected in the JavaScript-capable browser to TodayOJ during a displayed EUR-Lex service outage; requested legislative content was absent.|Workflow operator / Legal|SRC-OJ-01,SRC-OJ-02|
|BLOCK-AMEND|Amending act OJ L 2026/1744 route redirected in the JavaScript-capable browser to TodayOJ during a displayed EUR-Lex service outage; the requested act was absent.|Workflow operator / Legal|SRC-AMEND-01,SRC-AMEND-02|
|BLOCK-CONSOLIDATED|Requested July 27 dated consolidation was absent from a redirected Official Journal listing.|Workflow operator / Legal|SRC-CONSOLIDATED-01,SRC-CONSOLIDATED-02|
|CONFLICT-003|SYSTEMS says complete with visible label; REC-003 reports possible published-copy provenance loss. Preserve both reports.|Communications|FACT-AI-003,REC-003,POL-SYNTHETIC|
|CONFLICT-007|Register and reported capture say no notice while the owner says a banner exists. A stylized graphic does not settle what visitors understand.|Marketing|FACT-AI-007,REC-008,POL-NOTICE|
|CONFLICT-FAQ|Current FAQ overview refers to 50(2) for interaction; its later answer refers to 50(1). Binding cross-check is unavailable.|Legal|GUIDE-FAQ-CONFLICT,BLOCK-OJ,BLOCK-AMEND|
|GAP-HISTORY|Sheets modified August 28 with empty revision lists do not prove exact August 26 workbook versions.|Operations|SRC-SYSTEMS-01,SRC-EVIDENCE-01,SRC-CALENDAR-01|
|GAP-005|Current development, branding, release, market entry and biometric/emotion/category facts remain unknown; human adjudication does not establish them.|Assessment Operations|FACT-AI-005,REC-005,REC-006|
|GAP-008-PROVENANCE|Visible label is reported but machine-readable provenance is untested; supplier entry remains an owner report.|Communications|FACT-AI-008,REC-009,FACT-MARKET-003-008,POL-SYNTHETIC|
|GAP-008-EXCEPTION|Draft REC-010 has no Legal approval or expiry. It grants no exception.|Communications / Legal|REC-010,POL-EXCEPTION|
|GAP-002|Recipient disclosure evidence is missing despite the reported private staff drafting and individual human-edited email flow. Statutory scope remains withheld.|Admissions|FACT-AI-002,REC-002,POL-DRAFT|
|GAP-004|No first-interaction notice is reported; actual onboarding and accessibility proof were not captured.|Learning Experience|FACT-AI-004,REC-004,POL-NOTICE|
|GAP-PROOF|Register labels and owner context do not independently verify screenshots, metadata, releases, exception approval or historical deployment.|Operations|SRC-EVIDENCE-01,SRC-POLICY-03|
|GAP-NOTION|Native connector URL and UUID reads returned 404; the separate fresh published Notion UI read succeeded. Integration setup remains unresolved.|Workflow operator|SRC-POLICY-01,SRC-POLICY-02,SRC-POLICY-03|

## Proposed actions and calendar

All proposals remain **pending**; source status grants no approval or closure. Omitted actions have no event.

| Action / system | Proposal | Owner / proposed date | Source status / reviewer | Basis |
|---|---|---|---|---|
|ACT-001 / AI-004|Add and verify first-interaction AI notice|Learning Experience / 2026-09-04|planned / operations|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-004-NOTICE|
|ACT-002 / AI-007|Resolve disclosure evidence conflict|Marketing / 2026-09-03|open / operations|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-007-NOTICE|
|ACT-003 / AI-002|Confirm recipient disclosure practice|Admissions / 2026-09-08|open / legal|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-002-DRAFT|
|ACT-004 / AI-003|Verify machine-readable provenance after publishing|Communications / 2026-09-10|open / operations|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-003-SYNTHETIC|
|ACT-005 / AI-005|Refresh provider-role and release evidence|Assessment Operations / 2026-09-12|open / legal|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-005-EVIDENCE|
|ACT-006 / AI-008|Complete provenance test|Communications / 2026-09-09|open / operations|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-008-SYNTHETIC|
|ACT-007 / AI-008|Review exception request|Legal / 2026-09-15|blocked / legal|SRC-CALENDAR-01,POL-AUTHORITY,IMP-AI-008-EXCEPTION|
|ACT-008 / ALL|Quarterly AI register evidence review|Operations / 2026-10-02|scheduled / operations|SRC-CALENDAR-01,POL-AUTHORITY,POL-EVIDENCE,GAP-HISTORY,GAP-PROOF|
|PROP-RESTORE-AUTHORITY / ALL|Restore binding-source access and perform a new fresh review|Workflow operator / Legal / undated; omitted pending Operations|draft / legal|BLOCK-OJ,BLOCK-AMEND,BLOCK-CONSOLIDATED,POL-AUTHORITY,IMP-AI-001-AUTHORITY,IMP-AI-002-AUTHORITY,IMP-AI-003-AUTHORITY,IMP-AI-004-AUTHORITY,IMP-AI-005-AUTHORITY,IMP-AI-006-AUTHORITY,IMP-AI-007-AUTHORITY,IMP-AI-008-AUTHORITY|

## Legal and Operations review requests

Requests remain **pending and unsent**, bound to this run, captured versions and final drafts in `review-request-bindings.json`. Snapshot 06 retains full evidence. Identical questions share a row.

| Required reviewer / question | Request → subjects |
|---|---|
|Legal: Identify the missing authority and system facts required to review this August 26 use. Statutory actor, paragraph, exception and timing conclusions are withheld until a new successful source run. Assess the reported internal controls and historical limits without granting approval.|REQ-AI-001-LEGAL→AI-001/IMP-AI-001-AUTHORITY; REQ-AI-002-LEGAL→AI-002/IMP-AI-002-AUTHORITY; REQ-AI-003-LEGAL→AI-003/IMP-AI-003-AUTHORITY; REQ-AI-004-LEGAL→AI-004/IMP-AI-004-AUTHORITY; REQ-AI-005-LEGAL→AI-005/IMP-AI-005-AUTHORITY; REQ-AI-006-LEGAL→AI-006/IMP-AI-006-AUTHORITY; REQ-AI-007-LEGAL→AI-007/IMP-AI-007-AUTHORITY; REQ-AI-008-LEGAL→AI-008/IMP-AI-008-AUTHORITY|
|Operations: Confirm this action owner and recorded proposal date, or supply a supported alternative bound to the reviewed draft. Existing status and elapsed date are not activation or closure. An undated action remains undated until authorized review.|REQ-ACT-001-OPS→AI-004/ACT-001; REQ-ACT-002-OPS→AI-007/ACT-002; REQ-ACT-003-OPS→AI-002/ACT-003; REQ-ACT-004-OPS→AI-003/ACT-004; REQ-ACT-005-OPS→AI-005/ACT-005; REQ-ACT-006-OPS→AI-008/ACT-006; REQ-ACT-007-OPS→AI-008/ACT-007; REQ-ACT-008-OPS→ALL/ACT-008; REQ-PROP-RESTORE-AUTHORITY-OPS→ALL/PROP-RESTORE-AUTHORITY|
|Legal: Review the bound action as fact collection or review preparation. Any statutory conclusion awaits the missing binding acts; an exception requires actual owner, rationale, expiry and authorized approval. This request grants no approval.|REQ-ACT-003-LEGAL→AI-002/ACT-003; REQ-ACT-005-LEGAL→AI-005/ACT-005; REQ-ACT-007-LEGAL→AI-008/ACT-007; REQ-PROP-RESTORE-AUTHORITY-LEGAL→ALL/PROP-RESTORE-AUTHORITY|
|Legal: After fresh original-act, amendment and dated-consolidation access succeeds, verify paragraph operations, operative dates and any actor-specific transition. Resolve the conflicting FAQ references against those acts. Neither old captures nor current guidance can approve this blocked run.|REQ-AUTHORITY-LEGAL→ALL|

## Limitations

- Required original legislation and amendment were not retrieved in this run. The consolidation also failed. Statutory applicability, actor duties, exceptions and operative timing are withheld; no prior-run content or advisory summary replaces them.
- Every route was attempted freshly after this run began. Source records separate actual retrieval times from the fixed August 26, 2026 review date and Dublin as-of time.
- Notion connector URL and UUID reads failed 404. A separate fresh native read of the original published Notion page supplied policy and context; integration access remains unresolved.
- August AI-POL-2026-08-15 is distinct from September 12-authored RC-CONTEXT-2026-09-12-R1 describing August 26 observations. Retrospective owner context is not contemporaneous deployment proof.
- Native Sheets were modified August 28 and returned empty revision lists. Dated rows support bounded retrospective proposals, not verified exact August 26 workbook versions.
- Referenced screenshots, publication metadata, release notices and exception records were not independently retrieved. Register labels and owner reports cannot establish compliance or approval.
- Current advisory page versions are not independently established as exact August 26 versions. The FAQ retains conflicting paragraph references.
- Legal owns interpretation and exceptions; Operations owns activation, approved dates and closure. All requests remain pending and unsent. No verified feedback channel or facilitator pre-work verification was supplied.
- Recorded September and October 2 proposed dates were future to the assigned review date but elapsed at actual October 8 local retrieval. Preserve the retrospective proposals without invented rescheduling.
- This run also retains the LAW reader HTTP 429 failure and its fresh complete browser recovery. Three incomplete navigation observations were retained as diagnostic-only failures before the loaded wrong-document checks. No human-verification prompt appeared.
- Pinned Cisco AI Skill Scanner 2.0.13 and pipx remain absent; installation method requires user choice under installed scanner guidance. Automated security scanning remains unperformed.
- Earlier real runs, including failed artifacts and a validated partial review, are retained under history. Their captures are not source evidence for this run.

## Recorded workflow decisions

Full concerns, options, rationale and tradeoffs remain in snapshots 03–06.

| Decision | Recorded concern | Basis |
|---|---|---|
|DEC-AUTHORITY|Required legal identity and historical basis cannot be verified from the returned live content.|BLOCK-OJ,BLOCK-AMEND,BLOCK-CONSOLIDATED,GUIDE-LAW,GUIDE-FAQ-CONFLICT|
|DEC-RUNTIME|Native credentials are held by the connected agent, not the shell helper.|SRC-SYSTEMS-01,SRC-POLICY-03|
|DEC-HISTORY|Separate retrospective company reports from verified historical proof.|GAP-HISTORY,GAP-PROOF,FACT-SCOPE,BLOCK-OJ,BLOCK-AMEND|
|DEC-IMPACT|Separate blocked statutory questions from sourced internal controls.|BLOCK-OJ,BLOCK-AMEND,POL-AUTHORITY,POL-NOTICE,POL-SYNTHETIC,POL-EVIDENCE|
|DEC-ACTIONS|Preserve commitments while restricting publication to nondependent pending proposals.|SRC-CALENDAR-01,POL-AUTHORITY,POL-EXCEPTION,BLOCK-OJ,BLOCK-AMEND|
