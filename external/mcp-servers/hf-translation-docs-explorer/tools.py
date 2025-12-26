from __future__ import annotations

from typing import Any, Dict

from services import (
    build_project_catalog,
    build_search_response,
    build_missing_list_response,
    build_outdated_list_response,
)


def list_projects() -> Dict[str, Any]:
    return build_project_catalog(default=None)


def search_files(
    project: str,
    lang: str,
    limit: float | int,
    include_status_report: bool,
) -> Dict[str, Any]:
    return build_search_response(
        project=project,
        lang=lang,
        limit=int(limit or 1),
        include_status_report=bool(include_status_report),
    )


def list_missing_files(
    project: str,
    lang: str,
    limit: float | int,
) -> Dict[str, Any]:
    return build_missing_list_response(
        project=project,
        lang=lang,
        limit=int(limit or 1),
    )


def list_outdated_files(
    project: str,
    lang: str,
    limit: float | int,
) -> Dict[str, Any]:
    return build_outdated_list_response(
        project=project,
        lang=lang,
        limit=int(limit or 1),
    )
