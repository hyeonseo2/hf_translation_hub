#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable


def _load_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _extract_payload(raw_response: str) -> Any:
    lines = [line for line in raw_response.splitlines() if line.startswith("data: ")]
    payload = (lines[-1][6:] if lines else raw_response).strip()
    payload_obj = _load_json(payload)
    if payload_obj is None:
        raise ValueError("MCP payload is not valid JSON.")

    if isinstance(payload_obj, dict) and "result" in payload_obj:
        result = payload_obj.get("result")
        if isinstance(result, dict) and result.get("content"):
            raw_text = result["content"][0].get("text", "")
        else:
            raw_text = result
    else:
        raw_text = payload_obj

    if isinstance(raw_text, str):
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("MCP payload had an empty result body.")
        parsed = _load_json(raw_text)
        if parsed is not None:
            return parsed

    return raw_text


def _extract_files(root: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    files = (
        root.get("files")
        or root.get("result", {}).get("files")
        or root.get("data", {}).get("files")
        or root.get("items")
        or []
    )
    if not isinstance(files, list):
        return []
    return files


def _date_only(value: Any) -> str | None:
    if not value:
        return None
    return str(value).split(" ")[0]


def _extract_source_url(path: str | None, file_entry: Dict[str, Any]) -> str | None:
    if path:
        normalized = path
        if normalized.startswith("docs/source/en/"):
            normalized = normalized[len("docs/source/en/") :]
        if normalized.endswith(".md"):
            normalized = normalized[:-3]
        return f"https://huggingface.co/docs/transformers/{normalized}"
    return file_entry.get("source_url") or file_entry.get("url") or file_entry.get("source")


def _normalize_snapshot(root: Dict[str, Any]) -> Dict[str, Any]:
    files_output = []
    for entry in _extract_files(root):
        if not isinstance(entry, dict):
            continue
        metadata = entry.get("metadata") or {}
        path = entry.get("path") or metadata.get("path") or entry.get("file_path") or entry.get("source_path")
        status = metadata.get("status") or entry.get("status") or entry.get("translation_status") or entry.get("state")
        if not path or not status:
            continue
        files_output.append(
            {
                "path": path,
                "status": status,
                "last_commit_date": _date_only(
                    metadata.get("ko_base_commit")
                    or entry.get("last_commit_date")
                    or entry.get("last_commit")
                    or entry.get("last_updated")
                ),
                "source_url": _extract_source_url(path, entry),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": root.get("project")
        or root.get("arguments", {}).get("project")
        or root.get("status_report", {}).get("project")
        or "transformers",
        "language": root.get("lang")
        or root.get("arguments", {}).get("lang")
        or root.get("status_report", {}).get("lang")
        or "ko",
        "files": files_output,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize MCP search results into a snapshot JSON payload.",
    )
    parser.add_argument(
        "--input",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Input file containing the raw MCP response (defaults to stdin).",
    )
    parser.add_argument(
        "--output",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Output file for the normalized snapshot JSON (defaults to stdout).",
    )
    args = parser.parse_args()

    raw_response = args.input.read()
    if not raw_response:
        raise ValueError("No response content provided.")

    payload = _extract_payload(raw_response)
    if not isinstance(payload, dict):
        raise ValueError("Parsed MCP payload did not resolve to a JSON object.")

    normalized = _normalize_snapshot(payload)
    json.dump(normalized, args.output, ensure_ascii=False, indent=2)
    args.output.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - surface errors for callers
        print(str(exc), file=sys.stderr)
        raise
