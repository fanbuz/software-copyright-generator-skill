#!/usr/bin/env python3
"""Service adapter for running one workflow stage from a job manifest."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import traceback
from pathlib import Path
from typing import Any, Callable

from analyze_project import analyze
from build_docx_from_md import build_all, confirmation_issues
from capture_screenshots import collect_manual_screenshots
from common import ensure_dir, read_json, write_json
from extract_code_material import extract
from generate_application_info import build_fields, require_confirmed_business, write_application_md
from generate_business_context import build_evidence, load_model_context, normalize_model_context, write_context_md, write_evidence_md, write_model_template
from generate_input_form import write_preflight_form
from generate_manual_draft import write_manual
from propose_code_selection import all_candidate_lines, build_candidates, selection_stats, write_selection_md
from review_three_piece_package import review_package


STAGES = {"preflight", "scan", "business", "code-selection", "draft", "screenshots", "build", "review"}


class StageStop(Exception):
    def __init__(self, message: str, outputs: dict[str, str] | None = None):
        super().__init__(message)
        self.outputs = outputs or {}


def manifest_error(message: str) -> dict[str, Any]:
    return {"ok": False, "requires_user_input": False, "error": message}


def require_path(data: dict[str, Any], field: str) -> Path:
    value = str(data.get(field) or "").strip()
    if not value:
        raise ValueError(f"manifest missing required field: {field}")
    return Path(value)


def require_text(data: dict[str, Any], field: str) -> str:
    value = str(data.get(field) or "").strip()
    if not value:
        raise ValueError(f"manifest missing required field: {field}")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("schema_version") != "software-copyright-job.v1":
        raise ValueError("manifest schema_version must be software-copyright-job.v1")
    return data


def stage_preflight(manifest: dict[str, Any]) -> dict[str, Any]:
    workdir = ensure_dir(require_path(manifest, "workdir"))
    outputs = write_preflight_form(workdir)
    raise StageStop("preflight input required", outputs)


def stage_scan(manifest: dict[str, Any]) -> dict[str, Any]:
    project = require_path(manifest, "project_dir")
    workdir = ensure_dir(require_path(manifest, "workdir"))
    out = workdir / "analysis/project.json"
    ensure_dir(out.parent)
    result = analyze(project)
    write_json(out, result)
    return {"analysis": str(out)}


def stage_business(manifest: dict[str, Any]) -> dict[str, Any]:
    project = require_path(manifest, "project_dir")
    workdir = ensure_dir(require_path(manifest, "workdir"))
    software_name = require_text(manifest, "software_name")
    analysis_path = Path(manifest.get("analysis") or workdir / "analysis/project.json")
    analysis = read_json(analysis_path)
    draft_dir = ensure_dir(workdir / "草稿")
    web_notes = ""
    if manifest.get("web_notes"):
        web_notes = Path(manifest["web_notes"]).read_text(encoding="utf-8")
    evidence = build_evidence(project, analysis, software_name, web_notes)
    evidence_json = draft_dir / "业务理解证据.json"
    evidence_md = draft_dir / "业务理解证据.md"
    write_json(evidence_json, evidence)
    write_evidence_md(evidence_md, evidence)
    model_context = manifest.get("model_context")
    if not model_context:
        template = draft_dir / "业务理解模型稿模板.json"
        write_model_template(template, evidence)
        raise StageStop("business model context required", {"evidence": str(evidence_md), "template": str(template)})
    context = normalize_model_context(load_model_context(Path(model_context)), evidence, web_notes)
    context_json = draft_dir / "业务理解.json"
    context_md = draft_dir / "业务理解.md"
    write_json(context_json, context)
    write_context_md(context_md, context)
    raise StageStop("business confirmation required", {"business_json": str(context_json), "business_md": str(context_md)})


def stage_code_selection(manifest: dict[str, Any]) -> dict[str, Any]:
    project = require_path(manifest, "project_dir")
    workdir = ensure_dir(require_path(manifest, "workdir"))
    draft_dir = ensure_dir(workdir / "草稿")
    candidates = build_candidates(project)
    target_pages = int(manifest.get("target_pages") or 60)
    lines_per_page = int(manifest.get("lines_per_page") or 50)
    target_lines = target_pages * lines_per_page
    stats = selection_stats(candidates)
    candidate_lines = all_candidate_lines(candidates)
    selected_pages = (stats["selected_lines"] + lines_per_page - 1) // lines_per_page if stats["selected_lines"] else 0
    all_pages = (candidate_lines + lines_per_page - 1) // lines_per_page if candidate_lines else 0
    data = {
        "project_root": str(project.resolve()),
        "schema_version": "code-selection.v1",
        "selection_required": True,
        "model_selection_required": True,
        "confirmation_required": True,
        "user_confirmed": False,
        "target_pages": target_pages,
        "lines_per_page": lines_per_page,
        "target_lines": target_lines,
        "estimated_selected_lines": stats["selected_lines"],
        "estimated_selected_pages": selected_pages,
        "estimated_all_candidate_lines": candidate_lines,
        "estimated_all_candidate_pages": all_pages,
        "confirmation_stage": "code-selection",
        "next_action": "请由模型填写 selected、start_line、end_line 和 model_reason，再让用户确认。",
        "files": candidates,
    }
    selection_json = draft_dir / "代码文件选择.json"
    selection_md = draft_dir / "代码文件候选清单.md"
    write_json(selection_json, data)
    write_selection_md(selection_md, data)
    raise StageStop("code selection confirmation required", {"selection_json": str(selection_json), "selection_md": str(selection_md)})


def stage_draft(manifest: dict[str, Any]) -> dict[str, Any]:
    project = require_path(manifest, "project_dir")
    workdir = ensure_dir(require_path(manifest, "workdir"))
    software_name = require_text(manifest, "software_name")
    version = str(manifest.get("version") or "V1.0")
    draft_dir = ensure_dir(workdir / "草稿")
    analysis = read_json(Path(manifest.get("analysis") or workdir / "analysis/project.json"))
    business = read_json(Path(manifest.get("business_context") or draft_dir / "业务理解.json"))
    require_confirmed_business(business)
    selection = Path(manifest.get("code_selection") or draft_dir / "代码文件选择.json")
    code_manifest = extract(project, draft_dir, software_name, version, 50, selection)
    answers = read_json(Path(manifest["answers"])) if manifest.get("answers") else {}
    fields = build_fields(analysis, code_manifest, software_name, version, answers, business)
    application_md = draft_dir / "申请表信息.md"
    write_application_md(application_md, fields, analysis, code_manifest, business)
    manual_md = draft_dir / "操作手册.md"
    write_manual(manual_md, analysis, software_name, version, business)
    raise StageStop(
        "application fields and markdown confirmation required",
        {
            "code_manifest": str(draft_dir / "代码提取清单.json"),
            "application_md": str(application_md),
            "manual_md": str(manual_md),
        },
    )


def stage_screenshots(manifest: dict[str, Any]) -> dict[str, Any]:
    workdir = ensure_dir(require_path(manifest, "workdir"))
    manual_dir = manifest.get("manual_screenshot_dir")
    if not manual_dir:
        raise StageStop("manual_screenshot_dir required for user-supplied screenshots")
    result = collect_manual_screenshots(Path(manual_dir), workdir / "截图")
    return {"manifest": str(workdir / "截图/截图清单.json"), "status": str(result.get("status"))}


def stage_build(manifest: dict[str, Any]) -> dict[str, Any]:
    workdir = ensure_dir(require_path(manifest, "workdir"))
    issues = confirmation_issues(workdir)
    if issues:
        raise StageStop("formal build confirmation gates are incomplete", {"issues": "\n".join(issues)})
    result = build_all(workdir, require_text(manifest, "software_name"), str(manifest.get("version") or "V1.0"), bool(manifest.get("skip_preview", True)))
    return {"report": result["report"], "outputs": result["outputs"]}


def stage_review(manifest: dict[str, Any]) -> dict[str, Any]:
    final_dir = Path(manifest.get("final_dir") or require_path(manifest, "workdir") / "正式资料")
    result = review_package(final_dir, require_text(manifest, "software_name"), str(manifest.get("version") or "V1.0"), list(manifest.get("forbidden_terms") or []))
    return {"review": result}


STAGE_RUNNERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "preflight": stage_preflight,
    "scan": stage_scan,
    "business": stage_business,
    "code-selection": stage_code_selection,
    "draft": stage_draft,
    "screenshots": stage_screenshots,
    "build": stage_build,
    "review": stage_review,
}


def run_stage(manifest_path: Path, stage: str) -> tuple[int, dict[str, Any]]:
    if stage not in STAGES:
        return 2, manifest_error(f"unknown stage: {stage}")
    try:
        manifest = load_manifest(manifest_path)
        runner = STAGE_RUNNERS[stage]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            outputs = runner(manifest)
        payload = {
            "ok": True,
            "stage": stage,
            "requires_user_input": False,
            "outputs": outputs,
        }
        captured = buffer.getvalue().strip()
        if captured:
            payload["logs"] = captured.splitlines()
        return 0, payload
    except StageStop as exc:
        return 10, {
            "ok": False,
            "stage": stage,
            "requires_user_input": True,
            "next_action": str(exc),
            "outputs": exc.outputs,
        }
    except Exception as exc:
        return 1, {
            "ok": False,
            "stage": stage,
            "requires_user_input": False,
            "error": str(exc),
            "traceback": traceback.format_exc(limit=5),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=sorted(STAGES))
    args = parser.parse_args()

    code, payload = run_stage(args.manifest, args.stage)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
