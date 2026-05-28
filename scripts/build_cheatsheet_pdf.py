#!/usr/bin/env python3
"""Build the OpenClaw RL attempter/reviewer cheatsheet PDF.

Distilled from 382 universe-grounded audits across 5 batches.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether,
)

OUT = Path("/Users/vishal.kushwaha/Documents/Openclaw_RL copy/OpenClaw_Cheatsheet.pdf")

# ---------- styles ----------
styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title", parent=styles["Title"],
    fontSize=22, textColor=colors.HexColor("#1f3864"),
    spaceAfter=4, alignment=1,
)
SUBTITLE = ParagraphStyle(
    "Subtitle", parent=styles["Normal"],
    fontSize=11, textColor=colors.HexColor("#5e5e5e"),
    spaceAfter=10, alignment=1, italics=True,
)
H1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=17, textColor=colors.HexColor("#1f3864"),
    spaceBefore=6, spaceAfter=8,
    borderPadding=4, leftIndent=0,
)
H2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=13, textColor=colors.HexColor("#2e5395"),
    spaceBefore=10, spaceAfter=4,
)
H3 = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontSize=11, textColor=colors.HexColor("#444444"),
    spaceBefore=6, spaceAfter=3, fontName="Helvetica-Bold",
)
BODY = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=9, leading=12, spaceAfter=2,
)
BODY_SMALL = ParagraphStyle(
    "BodySmall", parent=styles["Normal"],
    fontSize=8, leading=10, spaceAfter=2,
)
BULLET = ParagraphStyle(
    "Bullet", parent=BODY,
    leftIndent=12, bulletIndent=2, spaceAfter=2,
)
CALLOUT = ParagraphStyle(
    "Callout", parent=BODY,
    fontSize=9, leading=12, textColor=colors.HexColor("#9c2222"),
    fontName="Helvetica-Bold", spaceAfter=4,
)

FAIL_BG = colors.HexColor("#ffe5e5")
NONFAIL_BG = colors.HexColor("#fff7d6")
PASS_BG = colors.HexColor("#e2f0d9")
HDR_BG = colors.HexColor("#1f3864")
ALT_BG = colors.HexColor("#f2f2f2")


def bullet(text: str) -> Paragraph:
    return Paragraph(f"&bull;&nbsp;&nbsp;{text}", BULLET)


def check(text: str) -> Paragraph:
    return Paragraph(f"&#9744;&nbsp;&nbsp;{text}", BULLET)


def hr() -> Spacer:
    return Spacer(1, 6)


# ---------- page 1: cover + master checklist ----------
def page_cover():
    story = []
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("OpenClaw RL — QC Cheatsheet", TITLE))
    story.append(Paragraph(
        "For attempters & reviewers &nbsp;|&nbsp; "
        "Distilled from 382 universe-grounded audits across 5 batches",
        SUBTITLE,
    ))
    story.append(hr())

    story.append(Paragraph("What this cheatsheet covers", H2))
    story.append(Paragraph(
        "Five batches (test_v3, L12, test4, L11, L4 — 382 tasks) were audited with universe grounding. "
        "These pages distill the recurring failure modes into actionable checklists for the three artifact types "
        "you control: <b>prompts, rubrics, tests</b>. Every entry maps to a real defect that drove a Score-2 fail "
        "or near-miss. Use the page-specific checklists before submitting.",
        BODY,
    ))
    story.append(hr())

    story.append(Paragraph("Headline failure rates (your batch is unlikely to be better)", H2))
    rows = [
        ["Batch", "Tasks", "% Score 2", "% Score 4-5", "Top failure mode"],
        ["test_v3",   "4",   "75%",  "25%",  "Aggressive G5 / DO-leak flagging"],
        ["L12",       "87",  "56%",  "37%",  "Rubric overfits DO-only section headers"],
        ["test4",     "20",  "40%",  "55%",  "Rubric weight-sign inversions"],
        ["L11",       "103", "55%",  "36%",  "Rubric / prompt contradiction"],
        ["L4 (att.)", "168", "47%",  "44%",  "CB justifications defend unrequested rubric"],
    ]
    t = Table(rows, colWidths=[1.0*inch, 0.7*inch, 0.85*inch, 0.85*inch, 3.0*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8.5),
        ("ALIGN",      (1, 1), (3, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#bfbfbf")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(hr())

    story.append(Paragraph("Master pre-submission checklist (1 minute)", H2))
    rows = [
        ["", "PROMPT", "RUBRIC", "TESTS"],
        ["1",
         "Every artifact name and section header you grade is in the opening_prompt OR in a workspace file you tell the model to read",
         "Each criterion is defensible against opening_prompt alone — not against desired_outcome",
         "No hardcoded number contradicts the universe snapshot (recount sleep_logs, transactions, etc.)"],
        ["2",
         "If you say 'do not produce X yet' or 'keep in chat,' the rubric does NOT grade producing X",
         "Polarity matches intent: positive weight rewards good behavior; negative weight penalizes bad",
         "No EXPECTED_COUNTS hardcoded that contradict snapshots.json"],
        ["3",
         "Required files referenced are real (`rule.md`, `policy.md`, `output_spec.md`, attached PDFs/images)",
         "Atomicity: one constraint per criterion. Do not bundle 'X AND Y AND Z'",
         "No test requires an artifact the prompt explicitly forbids"],
        ["4",
         "Safety boundary, required tool channels, and recipients are explicit",
         "Safety tasks (`has_safety_issues=yes`) carry at least one negative-weight criterion",
         "Date comparisons include time component, not just first 10 chars"],
        ["5",
         "Numeric thresholds and dates are defined or derivable from universe data",
         "Justifications are filled in, match their criterion titles, and are not 'correct it is' boilerplate",
         "Filename-locked tests are only used when the filename is in opening_prompt"],
    ]
    t = Table(rows, colWidths=[0.25*inch, 2.05*inch, 2.05*inch, 2.05*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7.5),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ALIGN",      (0, 0), (0, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#bfbfbf")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(hr())

    story.append(Paragraph(
        "<b>Page guide:</b> "
        "P2 = Prompt cheatsheet (attempter writing the task) &nbsp;|&nbsp; "
        "P3 = Rubric cheatsheet (CB grading) &nbsp;|&nbsp; "
        "P4 = Tests cheatsheet (verifier author) &nbsp;|&nbsp; "
        "P5 = 21-dimension quick reference + cardinal rules",
        BODY_SMALL,
    ))
    story.append(PageBreak())
    return story


# ---------- page 2: PROMPT ----------
def page_prompt():
    story = []
    story.append(Paragraph("1. PROMPT cheatsheet", H1))
    story.append(Paragraph(
        "The opening prompt is the contract. Everything the rubric grades and every test asserts must trace back to "
        "the opening prompt OR a workspace file the model is explicitly told to read. If your rubric needs a section "
        "header the prompt doesn't mention, the prompt is incomplete (not the model wrong).",
        BODY,
    ))
    story.append(hr())

    story.append(Paragraph("Pre-submission checklist", H2))
    items = [
        "Every deliverable filename appears in the opening prompt or in a referenced workspace file",
        "Every required section heading or label vocabulary is named in the opening prompt",
        "Required tool channels (email, slack, calendar, fintrack, airtable, etc.) are named explicitly",
        "Forbidden actions are stated explicitly (e.g., 'do not send', 'do not change records', 'do not write files')",
        "Multi-turn gates (e.g., 'first review, then produce') are clear about which turn is the final deliverable",
        "Numeric thresholds (counts, percentages, dates, windows) are stated or derivable from universe data",
        "Privacy/safety boundaries (who can receive what) are explicit",
        "Source-of-truth files (rule.md, policy.md, policy.png, output_spec.md, *.pdf) are named for the model to read",
        "PII the model may legitimately see vs surface is distinguished",
        "Universe data the rubric depends on is reachable (no fabricated services like 'FinTrack' when only fintrack exists)",
    ]
    for it in items:
        story.append(check(it))
    story.append(hr())

    story.append(Paragraph("Top 8 prompt pitfalls (saw in 382 audits)", H2))
    pitfalls = [
        ("Prompt forbids files, rubric demands files",
         "Prompt says 'keep in chat' but rubric grades creation of `report.docx`. "
         "Saw on ~22 L4 tasks. Either remove the file requirement or remove the chat-only constraint."),
        ("Prompt says 'do not produce X yet'",
         "Prompt explicitly asks model to plan first; rubric penalizes the model for not producing the final deck "
         "this turn (`6a04c1b0...57a1`). Multi-turn gates and final-deliverable grading cannot coexist."),
        ("Rubric demands artifacts named only in desired_outcome",
         "Prompt asks for 'a memory file and a plan'; rubric checks for exact filenames "
         "`MEMORY.md`, `financial_health_report.md`, `financial_action_plan.md`. "
         "Specify the names in the prompt or accept any name."),
        ("Universe service name is fabricated",
         "Rubric references 'FinTrack' service (capital-F); universe only has `fintrack` service. "
         "Saw on `5835` (single-task audit). Verify service names against the actual universe before grading."),
        ("Prompt contradicts test/rubric",
         "Prompt says 'Please don't change anything in the records' but rubric/tests require specific MEMORY.md narrative "
         "(`...5817`). The model that follows the prompt automatically fails the rubric."),
        ("Filename in policy.png/PDF not surfaced",
         "Required filename (`colt_reply_draft.md`) lives only in an attached image the model must inspect. "
         "Make the rule explicit in the prompt body too, otherwise the model legitimately uses a different name."),
        ("Workspace file referenced but not actually present",
         "Prompt directs model to read `memory_seed.md` or `dr_mehta_brief_template.txt`; universe doesn't contain them. "
         "Model halts; rubric penalizes the halt. Either ship the file or remove the reference."),
        ("Casual phrasing graded as literal string",
         "Prompt asks for 'a clean one-page brief'; rubric grades exact 36-word/6-line cap and "
         "exact section labels like 'Open Questions'. Either codify the format in the prompt or relax the rubric."),
    ]
    for title, body in pitfalls:
        story.append(Paragraph(f"<b>{title}</b>", H3))
        story.append(Paragraph(body, BODY))
    story.append(hr())

    story.append(Paragraph("Quick hacks for attempters", H2))
    hacks = [
        "Before writing the rubric, list every concrete word/number you plan to grade. "
        "Every one must appear in the prompt body or a referenced workspace file. If not, fix the prompt first.",
        "Use 'must' / 'must not' / 'do not' for hard constraints. Reviewers and models both parse these consistently.",
        "If the prompt has multiple turns, label the final-deliverable turn explicitly: "
        "'In your final response, produce X'. Avoid ambiguity about which turn is graded.",
        "When you reference a workspace file (rule.md, policy.png), test that you have actually placed it in the universe.",
        "If the universe data conflicts with what the rubric assumes, fix the prompt or the universe — do not paper over with a rubric carve-out.",
    ]
    for h in hacks:
        story.append(bullet(h))
    story.append(PageBreak())
    return story


# ---------- page 3: RUBRIC ----------
def page_rubric():
    story = []
    story.append(Paragraph("2. RUBRIC cheatsheet", H1))
    story.append(Paragraph(
        "The most common Score-2 cause across all 382 audits is the rubric, not the model. "
        "<b>69 of 168 L4 tasks (41%) failed on [Fail - Incorrect Justification]</b> — the CB defending unrequested "
        "rubric criteria. Use this page to inoculate your rubric before submission.",
        BODY,
    ))
    story.append(hr())

    story.append(Paragraph("Pre-submission checklist", H2))
    items = [
        "Each criterion's evidence string is in the opening_prompt or a workspace file the model reads",
        "No criterion grades a desired_outcome-only token (section header, label vocabulary, exact filename)",
        "Weights are within {-5, -3, -1, +1, +3, +5} and match the severity definitions in reference/06_weight_definitions.md",
        "Polarity: positive criteria reward intended behavior; negative criteria penalize specific failure modes",
        "Atomicity: each criterion has exactly one assertion. 'X AND Y AND Z' is split into 3 criteria",
        "Safety task (`has_safety_issues=yes`)? At least one negative-weight criterion is present",
        "Justifications are filled in (not 'correct it is' / 'wrong it is') and reference real content from the model output",
        "Each justification matches its criterion title — no copy-paste mismatches across rows",
        "Hardcoded numbers (counts, totals, percentages) match the universe snapshot — recount them, do not trust the DO",
        "Spot checks per outcome group are <= 5; over-budget cells split into separate criteria",
        "No mere inversion: a negative criterion is meaningfully different from any positive criterion",
        "No overlap pairs unless the negative isolates a real failure mode the model actually exhibits",
    ]
    for it in items:
        story.append(check(it))
    story.append(hr())

    story.append(Paragraph("Top 10 rubric defects (from 382 audits)", H2))
    pitfalls = [
        ("DO-leak / G5 desired-outcome leak",
         "The #1 failure. Rubric grades exact section names, filenames, status labels that only appear in "
         "`desired_outcome`, not in the opening prompt. Routinely flips Score 4-5 to Score 2 via Dim 21."),
        ("Verbatim quotes the prompt didn't mandate",
         "E.g., 'likely deductible, verify with accountant', '[ANOMALY DETECTED]', 'Do not rely on it yet'. "
         "If the prompt asks for paraphrase, the rubric must allow paraphrase."),
        ("Hardcoded numbers contradict the universe",
         "Saw on 4+ tasks: rubric says '25 sleep_logs' when universe has 22; '12.5 days' when "
         "universe shows 19; 'Wells Fargo $30,290.95' that contradicts the DO's own 'exclude transfers' rule. "
         "Always recount."),
        ("Weight polarity inverted",
         "Saw on `...57b8` (3 positive structural requirements weighted -5/-5/-3) and "
         "`...57b3` (criterion 7 with +5 reward for active spousal financial deception). "
         "Verify each weight against intent."),
        ("Missing prompt-grounded Major criteria",
         "Rubric drops to 1-2 criteria when the prompt enumerated 6-8 deliverables. "
         "Triggers `[Fail - 10%+ Major Rubric Errors]`."),
        ("`[Fail - No Negative Criteria]` on safety tasks",
         "Safety task carries `has_safety_issues=yes` but has zero negative-weight criteria. Cardinal-rule Fail. "
         "Saw on 6 L11 + 3 L4 tasks."),
        ("Justifications that don't match the criterion",
         "CB pastes the same boilerplate (or content from a different task) across many criteria. "
         "Saw blatantly on `...580d` and `...a44a`."),
        ("Polarity-flipped on the model's correct behavior",
         "Rubric penalizes the model for following the prompt verbatim (e.g., for redaction the prompt demanded, "
         "or for using the 'ask branch' the prompt explicitly mentioned)."),
        ("Atomicity bundling",
         "'Each daily entry contains X and Y and Z' becomes one criterion that fails if any of X/Y/Z is missing. "
         "Discount rule moves these to Moderate, but bundles still inflate raw fail-rate."),
        ("Rubric grades artifacts the prompt forbids",
         "Prompt says no file writes; rubric grades file contents. "
         "Saw extensively on attempter-only L4 batch (22 'Model Skipped Artifact' Non-Fails)."),
    ]
    for title, body in pitfalls:
        story.append(Paragraph(f"<b>{title}</b>", H3))
        story.append(Paragraph(body, BODY))
    story.append(hr())

    story.append(Paragraph("Quick hacks for rubric authors", H2))
    hacks = [
        "Before writing each criterion, paste the opening prompt next to it and ask: "
        "'Could a careful model derive this requirement from the prompt alone?'",
        "If you must grade a structural detail (header, filename), name it in the prompt body — not just the DO.",
        "Use functional equivalence wherever you can: 'a section identifying side-business income' beats "
        "'a section with the header Side-Business Income'.",
        "Negative criteria are for behaviors the prompt explicitly forbids. If the prompt says 'don't include X', "
        "you can have a -3 or -5 for X. Otherwise leave it out.",
        "Each criterion is one assertion. Split bundled clauses into atomic rows.",
        "After writing, do one pass to check that justifications match titles. Copy-paste errors are the #1 "
        "Dim 21 fail mode after DO-leak.",
        "If the universe contains the canonical values (transaction totals, dates, contact info), reference them "
        "from the universe — don't fabricate hardcoded numbers.",
    ]
    for h in hacks:
        story.append(bullet(h))
    story.append(PageBreak())
    return story


# ---------- page 4: TESTS ----------
def page_tests():
    story = []
    story.append(Paragraph("3. TESTS cheatsheet", H1))
    story.append(Paragraph(
        "Tests are graded under Dim 13 (Incorrect Tests) and Dim 14 (Underfitted Tests). "
        "Attempter-only batches lack tests entirely, but reviewer batches consistently ship brittle or "
        "factually-wrong test suites. Use this page before submitting a verifier.",
        BODY,
    ))
    story.append(hr())

    story.append(Paragraph("Pre-submission checklist", H2))
    items = [
        "Every EXPECTED_COUNT was recomputed from the actual universe snapshot — not from the DO",
        "Date comparisons use the full timestamp, not the first 10 chars (slicing `r[0][:10]` is a bug)",
        "Substring assertions are not used where structural assertions (parse + check keys) would work",
        "No test requires an artifact the prompt explicitly forbids (file writes, sends, record changes)",
        "Filename-locked tests are only used when the filename is in opening_prompt",
        "Negative tests assert the model did NOT do the forbidden thing — not that it did a specific alternative",
        "Tests do not check for the model's specific phrasing when paraphrase satisfies the prompt",
        "Pass@k coverage: no test has 0/16 pass rate without a corresponding rubric criterion explaining why",
        "Each test isolates one constraint; failures point to a specific cause",
        "Tests cover the explicit prompt requirements — not desired_outcome-only specifics",
    ]
    for it in items:
        story.append(check(it))
    story.append(hr())

    story.append(Paragraph("Top 7 test defects (from audits)", H2))
    pitfalls = [
        ("Hardcoded EXPECTED_COUNTS that contradict the universe",
         "On `...5823`, 4 of 6 tests hardcoded `calendar.events=154` when `snapshots.json` says 224, plus a "
         "'13-service baseline' that doesn't exist in the bundle. 3/4 of the verifier was broken."),
        ("Date comparisons that drop the time",
         "`dates = [r[0][:10] for r in rows]` then asserts sorted. Two events on the same day in wrong order pass. "
         "Saw on `...57df`. Use the full timestamp."),
        ("Filename-locked when the filename isn't in the prompt",
         "8/13 tests assert exact filename `colt_reply_draft.md`; that filename only appears in `policy.png`. "
         "Either name the filename in the prompt or accept any filename matching a pattern."),
        ("Tests that contradict the prompt",
         "Prompt: 'Please don't change anything in the records.' Tests: 'MEMORY.md must contain narrative X.' "
         "(`...5817`). 8/10 tests are unsatisfiable for any compliant model."),
        ("Tests that fail clean trajectories",
         "`test_glenn_reply_remediated_not_left_sent` asserts both a trashed outbound AND a draft must exist. "
         "Only Model A's send-then-remediate path satisfies this. A correct trajectory that never sends would fail."),
        ("Underfitted tests with trivial keyword acceptance",
         "`test_conflicts_are_acknowledged` accepts the keyword 'tamales verdes' — which is one of the recipes "
         "the model will mention anyway. The test passes vacuously."),
        ("Tests that grade DO-only schema tokens",
         "Tests assert exact JSON keys (`weekly_volume_rank`, `cost_per_tss_point`, `matched_sonos_playlist`) "
         "defined only in desired_outcome. Either move those to the prompt or use structural checks."),
    ]
    for title, body in pitfalls:
        story.append(Paragraph(f"<b>{title}</b>", H3))
        story.append(Paragraph(body, BODY))
    story.append(hr())

    story.append(Paragraph("Quick hacks for test authors", H2))
    hacks = [
        "Run the verifier against a Silver-trajectory output first. If Silver fails, the verifier is wrong.",
        "For numeric assertions, prefer ranges or tolerances over exact equality unless the prompt mandates exact values.",
        "For ordering tests, use the full sort key (timestamp + tiebreaker), not a truncated substring.",
        "Negative tests should be precise about what is forbidden. 'Must not contain X' is good; "
        "'Must contain Y AND not contain X' is brittle.",
        "Cross-check expected counts against `snapshots.json` and the actual service JSON files in the universe.",
        "If a test has 0/16 pass rate in pass@k, treat it as broken-by-default and fix before submission.",
    ]
    for h in hacks:
        story.append(bullet(h))
    story.append(PageBreak())
    return story


# ---------- page 5: 21 dimensions + cardinal rules ----------
def page_reference():
    story = []
    story.append(Paragraph("4. 21 QC Dimensions — Quick Reference", H1))
    story.append(Paragraph(
        "From <i>reference/03_dimensions.md</i>. Lowest-dimension-wins: the worst-scoring dimension in scope is "
        "what binds the QC score. Knowing which dimension is most likely to bite you saves rework.",
        BODY,
    ))
    story.append(hr())

    rows = [
        ["#", "Dimension", "What it grades", "Common defect"],
        ["1",  "Scenario/Type Match",  "Task matches the assigned scenario",  "Multi-turn task tagged as single-turn"],
        ["2",  "Domain Match",         "Within delivery domain",              "Cross-domain leakage"],
        ["3",  "Universe Match",       "Persona universe is appropriate",     "Wrong persona for task type"],
        ["4",  "Source Documentation", "Source URL + screenshot + date",      "Missing screenshot or date"],
        ["5",  "Trajectory Validator", "Validator score >= 3/5",              "G1 prompt-coverage gap"],
        ["6",  "Prompt Feasibility",   "Model can complete with tools",       "Asks for .docx but only plain-text write"],
        ["7",  "Tool Availability",    "Required tools present",              "Phantom services in rubric"],
        ["8",  "Rubric Quality",       "Atomicity, weights, completeness",    "DO-leak, hardcoded numbers, polarity"],
        ["9",  "Rubric Coverage",      ">=85% of explicit prompt asks",       "1-criterion rubric for 8-deliverable prompt"],
        ["10", "Weight Distribution",  "Spread within {-5..+5}",              "All +5 or all -3"],
        ["11", "Safety Negative Crit.","Negatives present for safety tasks",  "0 negatives on has_safety_issues=yes"],
        ["12", "CB Evaluations",       "Per-criterion ratings correct",       "057ad pattern: blanket misreads"],
        ["13", "Test Correctness",     "Tests assert real prompt behavior",   "Hardcoded counts, broken date slice"],
        ["14", "Test Coverage",        "Tests cover prompt deliverables",     "Underfit on key constraints"],
        ["15", "Safety Annotations",   "F1-F8 categorization",                "Misclassified failure category"],
        ["16", "Action Tier",          "T0-T3 selection correct",             "T3 for reversible local writes"],
        ["17", "Failure Recognition",  "Model failure correctly identified",  "Model hallucination missed"],
        ["18", "Trajectory Validity",  "All turns valid",                     "Tool-call schema errors"],
        ["19", "Rubric Justifications","Aligned, non-placeholder",            "'correct it is' boilerplate"],
        ["20", "Action Tier Justification","Tier rationale present",          "Empty tier_justification"],
        ["21", "Justification Quality (pass@k gate)","Reasoning is correct",  "Defends DO-only tokens"],
    ]
    t = Table(rows, colWidths=[0.25*inch, 1.45*inch, 2.40*inch, 2.40*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HDR_BG),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 7),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (0, 0), (0, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#bfbfbf")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ALT_BG]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    story.append(hr())

    story.append(Paragraph("Cardinal rules (from qc_auditor.md)", H2))
    rules = [
        "<b>Lowest-dimension-wins.</b> One Fail in any in-scope dimension caps the score at 2. Catch your worst dimension early.",
        "<b>Evidence-grounded.</b> Every Fail tag must cite a specific criterion number and exact quote — no hand-waving.",
        "<b>Pass@k gate on Dim 21.</b> Justifications are only graded when ALL pass@k evals fail. Otherwise skip.",
        "<b>Atomicity discount.</b> Bundled-but-related Major flags discount to Moderate; under threshold becomes Non-Fail.",
        "<b>NEVER-fire tags.</b> `[Fail - No Negative Criteria]` is only valid when has_safety_issues=yes AND the rubric has 0 negative-weight criteria. Drop it in all other contexts.",
        "<b>`[Fail - Incorrect Evaluations]` was retired in v1.1.</b> Dim 12 misreads now cap at Score 3-4 via `[Non-Fail - Minor Incorrect Evaluations]`.",
        "<b>Universe grounding is non-optional.</b> Before flagging G5 or Dim 21, confirm via grep that the token is absent from services/*, policy files, and attached artifacts.",
        "<b>No em-dashes in audit output.</b> Style rule from the system prompt.",
    ]
    for r in rules:
        story.append(bullet(r))
    story.append(hr())

    story.append(Paragraph("Calibration anchors", H2))
    story.append(Paragraph(
        "Across the 10 human-validated tasks (from project-698318a4 QC validations 8 and 9): "
        "<b>5/10 exact score match</b>, <b>8/10 within-1 score point</b>, <b>2/10 off-by-2+</b>. "
        "Misses cluster on: aggressive G5 firing where universe artifacts would rescue, "
        "Dim 15-17 safety annotation gaps, and tag-bucket category confusion (Major vs Moderate).",
        BODY,
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<i>Generated from 382 universe-grounded audits across test_v3, L12, test4, L11, L4 (May 2026). "
        "OpenClaw QC Auditor v1.1 — synced to 2026-05-23 QC spec.</i>",
        BODY_SMALL,
    ))
    return story


def main():
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=LETTER,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
        title="OpenClaw RL — QC Cheatsheet",
        author="OpenClaw QC Auditor v1.1",
    )
    story = []
    story.extend(page_cover())
    story.extend(page_prompt())
    story.extend(page_rubric())
    story.extend(page_tests())
    story.extend(page_reference())
    doc.build(story)
    print(f"[ok] wrote {OUT}")


if __name__ == "__main__":
    main()
