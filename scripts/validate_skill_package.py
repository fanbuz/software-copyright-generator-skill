#!/usr/bin/env python3
"""Validate the skill package before release or service use."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


TEXT_EXTS = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}
REQUIRED_DIRS = ["agents", "references", "scripts"]
REQUIRED_FILES = ["SKILL.md", "README.md", "agents/openai.yaml", "LICENSE"]
SECRET_PATTERNS = [
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("generic password assignment", re.compile(r"(?i)\b(password|passwd|pwd|secret|token)\s*[:=]\s*['\"]?[^'\"\s]{12,}")),
    ("absolute user path", re.compile(r"/Users/[A-Za-z0-9._-]+/")),
]
RESIDUE_TERMS = [
    "simba",
    "ehr",
    "内部交流",
    "历史负担",
    "补强",
    "增强版",
]


def result(ok: bool = True) -> dict[str, Any]:
    return {"ok": ok, "errors": [], "warnings": []}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = read_text(path)
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def check_structure(root: Path) -> dict[str, Any]:
    out = result()
    for dirname in REQUIRED_DIRS:
        if not (root / dirname).is_dir():
            out["errors"].append(f"missing directory: {dirname}")
    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            out["errors"].append(f"missing file: {filename}")
    out["ok"] = not out["errors"]
    return out


def check_frontmatter(root: Path) -> dict[str, Any]:
    out = result()
    skill_path = root / "SKILL.md"
    data = parse_frontmatter(skill_path) if skill_path.exists() else {}
    for key in ("name", "description"):
        if not data.get(key):
            out["errors"].append(f"SKILL.md frontmatter missing required field: {key}")
    if data.get("name") and not re.fullmatch(r"[A-Za-z0-9-]+", data["name"]):
        out["errors"].append("SKILL.md frontmatter name must use letters, numbers, and hyphens")
    if data.get("name"):
        agent_text = read_text(root / "agents/openai.yaml") if (root / "agents/openai.yaml").exists() else ""
        if data["name"] not in read_text(root / "README.md") and data["name"] not in agent_text:
            out["warnings"].append("skill name is not mentioned in README.md or agents/openai.yaml")
    out["metadata"] = data
    out["ok"] = not out["errors"]
    return out


def check_python_syntax(root: Path) -> dict[str, Any]:
    out = result()
    for path in sorted((root / "scripts").glob("*.py")):
        try:
            ast.parse(read_text(path), filename=str(path))
        except SyntaxError as exc:
            rel = path.relative_to(root).as_posix()
            out["errors"].append(f"{rel}:{exc.lineno}:{exc.offset}: {exc.msg}")
    out["ok"] = not out["errors"]
    return out


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for base in [root / "README.md", root / "SKILL.md", root / "agents", root / "references", root / "scripts"]:
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lower() in TEXT_EXTS:
                    files.append(path)
    return sorted(set(files))


def check_sensitive_residue(root: Path) -> dict[str, Any]:
    out = result()
    for path in iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                out["errors"].append(f"{rel}:{line}: {label} pattern detected")
        if rel == "scripts/validate_skill_package.py":
            continue
        lowered = text.lower()
        for term in RESIDUE_TERMS:
            if term.lower() in lowered:
                out["warnings"].append(f"{rel}: review residue term: {term}")
    out["ok"] = not out["errors"]
    return out


def validate(root: Path) -> dict[str, Any]:
    checks = {
        "structure": check_structure(root),
        "frontmatter": check_frontmatter(root),
        "python_syntax": check_python_syntax(root),
        "sensitive_residue": check_sensitive_residue(root),
    }
    return {
        "ok": all(item["ok"] for item in checks.values()),
        "root": str(root),
        "checks": checks,
    }


def print_text_report(payload: dict[str, Any]) -> None:
    status = "PASS" if payload["ok"] else "FAIL"
    print(f"{status} skill package validation")
    for name, check in payload["checks"].items():
        print(f"- {name}: {'PASS' if check['ok'] else 'FAIL'}")
        for error in check.get("errors", []):
            print(f"  error: {error}")
        for warning in check.get("warnings", []):
            print(f"  warning: {warning}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = validate(args.root.resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text_report(payload)
    raise SystemExit(0 if payload["ok"] else 1)


if __name__ == "__main__":
    main()
