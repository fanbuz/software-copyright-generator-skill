#!/usr/bin/env python3
"""Review a software copyright DOCX package."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document


def docx_body_text(doc: Document) -> str:
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def docx_header_footer_text(doc: Document) -> str:
    parts = []
    for section in doc.sections:
        for area in [section.header, section.footer]:
            parts.extend(p.text for p in area.paragraphs)
            for table in area.tables:
                for row in table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
    return "\n".join(parts)


def count_term(text: str, term: str) -> int:
    if term.isascii() and term.isalnum():
        return len(re.findall(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text))
    return text.count(term)


def inspect_docx(path: Path, terms: list[str]) -> dict:
    doc = Document(str(path))
    body = docx_body_text(doc)
    header_footer = docx_header_footer_text(doc)
    combined = "\n".join([path.name, body, header_footer])
    return {
        "path": str(path),
        "exists": path.exists(),
        "size": path.stat().st_size,
        "paragraphs": len(doc.paragraphs),
        "tables": len(doc.tables),
        "rows_first_table": len(doc.tables[0].rows) if doc.tables else 0,
        "cols_first_row": len(doc.tables[0].rows[0].cells) if doc.tables and doc.tables[0].rows else 0,
        "images": sum(1 for rel in doc.part.rels.values() if "image" in rel.reltype),
        "term_counts": {term: count_term(combined, term) for term in terms},
        "body_term_counts": {term: count_term(body, term) for term in terms},
        "header_footer_term_counts": {term: count_term(header_footer, term) for term in terms},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True, type=Path)
    parser.add_argument("--software-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--forbidden", action="append", default=[])
    args = parser.parse_args()

    files = {
        "info": sorted(args.dir.glob(f"*信息采集表*{args.version}*.docx")),
        "manual": sorted(args.dir.glob(f"*用户手册*{args.version}*.docx")),
        "source": sorted(args.dir.glob(f"*源代码*{args.version}*.docx")),
    }
    terms = [args.software_name, args.version, *args.forbidden]
    result = {"dir": str(args.dir), "files": {}, "missing": [], "warnings": []}
    for kind, matches in files.items():
        if not matches:
            result["missing"].append(kind)
            continue
        info = inspect_docx(matches[0], terms)
        result["files"][kind] = info
        for forbidden in args.forbidden:
            if info["term_counts"].get(forbidden, 0) > 0:
                result["warnings"].append(f"{kind}: forbidden term remains: {forbidden}")
        for identity in [args.software_name, args.version]:
            if info["term_counts"].get(identity, 0) > 0 and (
                info["body_term_counts"].get(identity, 0) + info["header_footer_term_counts"].get(identity, 0) == 0
            ):
                result["warnings"].append(f"{kind}: {identity} only appears in filename, not body/header/footer")

    result["ok"] = not result["missing"] and all(
        item["term_counts"].get(args.software_name, 0) > 0 and item["term_counts"].get(args.version, 0) > 0
        for item in result["files"].values()
    ) and not any("forbidden term remains" in item for item in result["warnings"])
    result["strict_ok"] = result["ok"] and not result["warnings"]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
