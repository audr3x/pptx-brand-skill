#!/usr/bin/env python3
"""Check and build one eval task. Every call is logged as one attempt.

Usage: python3 evals/build.py --model <model> --task <task-id>

Reads evals/runs/<model>/<task>/outline.yaml and writes, next to it:
  PowerPoint tasks: deck.pptx
  Google Slides tasks: slides/creates.json, slides/fills.json, slides/fills-NN.json
  both: render/slide-N.png (Google Slides tasks render a PowerPoint built from the same
        outline, because the Slides batches cannot be rendered offline)
  attempts.jsonl: one line per call (step, exit code, error and warning counts)

The check runs with --prompt pointed at the task prompt and its fixtures, so dates and
figures the prompt never gave are warned about. After the build, scripts/readback.py
prints the visible text per slide and fails the attempt if outline text is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"


def target_for(task: str) -> str:
    spec = EVALS / "specs" / f"{task}.yaml"
    if not spec.is_file():
        raise SystemExit(f"unknown task {task!r}; see evals/tasks/")
    return yaml.safe_load(spec.read_text()).get("target", "pptx")


def sources_for(task: str) -> list[str]:
    """The task prompt plus any fixture it points at: everything the user gave the runner."""
    prompt = EVALS / "tasks" / f"{task}.md"
    found = re.findall(r"evals/tasks/fixtures/[\w./-]*\w", prompt.read_text())
    return [str(prompt.relative_to(ROOT))] + sorted({f for f in found if (ROOT / f).is_file()})


def run(cmd: list[str], env: dict | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300, env=env)
    return p.returncode, p.stdout + p.stderr


def render(pptx: Path, out: Path) -> int:
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        # Maps the template's "Archivo Light" family to Archivo at light weight so text wraps as in PowerPoint.
        env = {**os.environ, "FONTCONFIG_FILE": str(EVALS / "fonts.conf")}
        rc, _ = run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx)], env)
        pdf = Path(tmp) / (pptx.stem + ".pdf")
        if rc or not pdf.is_file():
            return 0
        run(["pdftoppm", "-png", "-r", "80", str(pdf), str(out / "slide")])
    pages = sorted(out.glob("slide-*.png"))
    for p in pages:
        p.rename(out / f"slide-{int(p.stem.split('-')[-1])}.png")
    return len(pages)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="folder name under evals/runs/, for example claude-opus-5.5")
    ap.add_argument("--task", required=True, help="task id, for example T01-kickoff-pptx")
    ap.add_argument("--rebuild", action="store_true",
                    help="refresh artifacts from the existing outline after a builder change; not logged as an attempt")
    args = ap.parse_args()
    target = target_for(args.task)
    run_dir = EVALS / "runs" / args.model / args.task
    outline = run_dir / "outline.yaml"
    if not outline.is_file():
        raise SystemExit(f"write the outline to {outline.relative_to(ROOT)} first")
    rel = str(outline.relative_to(ROOT))
    log = run_dir / "attempts.jsonl"
    attempt = sum(1 for _ in log.open()) + 1 if log.is_file() else 1

    prompts = [a for s in sources_for(args.task) for a in ("--prompt", s)]
    steps: list[tuple[str, list[str]]] = [("check", [sys.executable, "scripts/check_outline.py", "--target", target, *prompts, rel])]
    if target == "pptx":
        steps.append(("build_pptx", [sys.executable, "scripts/build_deck.py", rel, "-o", str(run_dir / "deck.pptx")]))
        preview = run_dir / "deck.pptx"
        built = preview
    else:
        slides = run_dir / "slides"
        steps.append(("build_creates", [sys.executable, "scripts/build_slides.py", rel, "--phase", "creates", "-o", str(slides / "creates.json")]))
        steps.append(("build_fills", [sys.executable, "scripts/build_slides.py", rel, "--phase", "fills", "--chunk", "40", "-o", str(slides / "fills.json")]))
        preview = run_dir / "preview.pptx"
        steps.append(("build_preview", [sys.executable, "scripts/build_deck.py", rel, "-o", str(preview)]))
        built = slides / "fills.json"
    steps.append(("readback", [sys.executable, "scripts/readback.py", rel, str(built.relative_to(ROOT)), "--show"]))

    record = {"attempt": attempt, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "target": target, "steps": []}
    rc_all = 0
    for name, cmd in steps:
        rc, out = run(cmd)
        print(f"$ {' '.join(Path(c).name if c == sys.executable else c for c in cmd)}\n{out.rstrip()}\n")
        record["steps"].append({
            "step": name,
            "rc": rc,
            "errors": sum(l.startswith("error:") for l in out.splitlines()),
            "warnings": sum(l.startswith("warning:") for l in out.splitlines()),
            "traceback": "Traceback" in out,
        })
        if name == "readback":
            record["steps"][-1]["missing"] = sum(l.startswith("missing:") for l in out.splitlines())
        if name == "check":
            record["steps"][-1]["unsourced"] = sum("is not in the prompt" in l for l in out.splitlines())
        if rc:
            rc_all = rc
            break
    if all(s["rc"] == 0 for s in record["steps"] if s["step"] != "readback") and preview.is_file():
        record["rendered_pages"] = render(preview, run_dir / "render")
        print(f"Rendered {record['rendered_pages']} PNGs to {(run_dir / 'render').relative_to(ROOT)}/")
    record["rc"] = rc_all
    if args.rebuild:
        print("rebuild only, attempt not logged")
        return rc_all
    with log.open("a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"attempt {attempt}: {'ok' if rc_all == 0 else 'failed'}")
    return rc_all


if __name__ == "__main__":
    raise SystemExit(main())
