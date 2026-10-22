#!/usr/bin/env python3
"""Throw hostile outlines at the outline check and both builders. Writes report.md.

For each case in cases/:
  - check_outline.py (errors / warnings)
  - build_deck.py -> .pptx, build_slides.py --dry-run -> request plan
  - verdict: CRASH if any tool prints a Python traceback, LOSS if outline text is missing
    from a built slide and the check said nothing about that slide, PLAN if the Slides
    request plan breaks a rule in evals/checks.py (for example bullets whose spacing
    collapses), OK otherwise.

Usage: python3 evals/adversarial/run.py [--render] [--out evals/adversarial/report.md]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
from checks import load_requests, slides_plan_problems  # noqa: E402

CASES = Path(__file__).resolve().parent / "cases"
SKIP_KEYS = {"layout", "intent", "image", "chart", "type"}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def leaf_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k not in SKIP_KEYS:
                out.extend(leaf_strings(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(leaf_strings(v))
    elif isinstance(value, str) and value.strip():
        out.append(value)
    return out


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout + p.stderr)


def pptx_slide_text(path: Path) -> list[str]:
    from pptx import Presentation

    texts = []
    for slide in Presentation(str(path)).slides:
        parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                parts.append(shape.text_frame.text)
            if getattr(shape, "has_table", False) and shape.has_table:
                parts.extend(c.text for row in shape.table.rows for c in row.cells)
        if slide.has_notes_slide:
            parts.append(slide.notes_slide.notes_text_frame.text)
        texts.append(norm(" ".join(parts)))
    return texts


def slides_plan_text(path: Path, n: int) -> list[str]:
    plan = json.loads(path.read_text())
    texts = [""] * n
    for r in plan.get("requests", []):
        ins = r.get("insertText")
        if not ins:
            continue
        m = re.match(r"wd_s(\d+)", ins["objectId"])
        if m and int(m.group(1)) <= n:
            texts[int(m.group(1)) - 1] += " " + norm(ins["text"])
    return texts


def missing_by_slide(outline: Any, built: list[str]) -> dict[int, list[str]]:
    missing: dict[int, list[str]] = {}
    slides = outline.get("slides") if isinstance(outline, dict) else None
    if not isinstance(slides, list):
        return missing
    for i, spec in enumerate(slides, 1):
        if i > len(built):
            missing[i] = ["<slide not built>"]
            continue
        lost = [s for s in leaf_strings(spec) if norm(s) not in built[i - 1]]
        if lost:
            missing[i] = lost
    return missing


def mentioned(slide: int, messages: str) -> bool:
    return re.search(rf"slide {slide}\b", messages) is not None


def evaluate(case: Path, render: bool, tmp: Path) -> dict[str, Any]:
    row: dict[str, Any] = {"case": case.stem}
    rc, out = run([sys.executable, "scripts/check_outline.py", str(case.relative_to(ROOT))])
    row["gate"] = "FAIL" if rc else "ok"
    row["gate_msgs"] = [l for l in out.splitlines() if l.startswith(("error:", "warning:"))]
    crash = "Traceback" in out
    try:
        import yaml

        outline = yaml.safe_load(case.read_text())
    except Exception:
        outline = None
    gate_text = "\n".join(row["gate_msgs"])

    pptx = tmp / f"{case.stem}.pptx"
    rc_p, out_p = run([sys.executable, "scripts/build_deck.py", str(case.relative_to(ROOT)), "-o", str(pptx)])
    row["pptx"] = "CRASH" if "Traceback" in out_p else ("ok" if rc_p == 0 else "error")
    row["pptx_msg"] = out_p.strip().splitlines()[-1] if out_p.strip() else ""
    plan = tmp / f"{case.stem}.json"
    rc_s, out_s = run([sys.executable, "scripts/build_slides.py", str(case.relative_to(ROOT)), "--dry-run", "-o", str(plan)])
    row["slides"] = "CRASH" if "Traceback" in out_s else ("ok" if rc_s == 0 else "error")
    row["slides_msg"] = out_s.strip().splitlines()[-1] if out_s.strip() else ""
    crash = crash or row["pptx"] == "CRASH" or row["slides"] == "CRASH"

    loss = []
    builder_warn = out_p + out_s
    if outline is not None and row["pptx"] == "ok":
        for i, lost in missing_by_slide(outline, pptx_slide_text(pptx)).items():
            if not mentioned(i, gate_text) and "Truncating" not in out_p:
                loss.append(f"pptx s{i}: {lost[0][:40]!r}")
    if outline is not None and row["slides"] == "ok":
        n = len(outline.get("slides") or [])
        for i, lost in missing_by_slide(outline, slides_plan_text(plan, n)).items():
            if not mentioned(i, gate_text) and "Truncating" not in out_s:
                loss.append(f"slides s{i}: {lost[0][:40]!r}")
    row["loss"] = loss
    row["plan"] = []
    if row["slides"] == "ok":
        problems = slides_plan_problems(load_requests(plan))
        row["plan"] = [f"{k}: {v[0]}" for k, v in problems.items() if v]
    # A builder that succeeds on an outline the gate rejects is fine; a gate that passes
    # an outline both builders reject is a gap.
    gap = row["gate"] == "ok" and row["pptx"] == "error" and row["slides"] == "error"
    if render and row["pptx"] == "ok":
        run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(pptx)])
        row["rendered"] = (tmp / f"{case.stem}.pdf").is_file()
    row["verdict"] = (
        "CRASH" if crash else "LOSS" if loss else "PLAN" if row["plan"] else "GAP" if gap else "OK"
    )
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "report.md")
    ap.add_argument("--keep", type=Path, help="keep built decks here")
    args = ap.parse_args()
    tmpdir = args.keep or Path(tempfile.mkdtemp())
    tmpdir.mkdir(parents=True, exist_ok=True)
    rows = [evaluate(c, args.render, tmpdir) for c in sorted(CASES.glob("*.y*ml"))]
    lines = [
        "# Adversarial outline report",
        "",
        "Generated by `python3 evals/adversarial/run.py`. CRASH = Python traceback. LOSS = outline text missing "
        "from a built slide with no warning for that slide. PLAN = the Slides request plan breaks a rule "
        "in `evals/checks.py` (fonts, colors, references, bullet spacing, image URLs). GAP = check passes but both builders fail.",
        "",
        "| Case | Verdict | Check | PowerPoint | Slides | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        notes = "; ".join(r["loss"][:2] or r["plan"][:2]) or (r["gate_msgs"][0] if r["gate_msgs"] else "")
        if r["pptx"] != "ok":
            notes = f"pptx: {r['pptx_msg']}" + (f"; {notes}" if notes else "")
        notes = notes.replace("|", "/")[:160]
        lines.append(f"| {r['case']} | {r['verdict']} | {r['gate']} ({len(r['gate_msgs'])}) | {r['pptx']} | {r['slides']} | {notes} |")
    counts = {v: sum(r["verdict"] == v for r in rows) for v in ("OK", "CRASH", "LOSS", "PLAN", "GAP")}
    lines += ["", "Totals: " + ", ".join(f"{k} {v}" for k, v in counts.items()), ""]
    args.out.write_text("\n".join(lines))
    print("\n".join(lines[-2:]))
    return 1 if counts["CRASH"] or counts["LOSS"] or counts["PLAN"] or counts["GAP"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
