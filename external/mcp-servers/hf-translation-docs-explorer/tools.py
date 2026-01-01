from __future__ import annotations

from typing import Any, Dict

from services import (
    build_project_catalog,
    build_search_response,
    build_missing_list_response,
    build_outdated_list_response,
)


def list_projects(toolCallId: str = "") -> Dict[str, Any]:
    """
    List all projects.

    Args:
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the list of projects.

    Raises:
        Exception: If the projects cannot be listed.
    """
    return build_project_catalog(default=None)


def search_files(
    project: str,
    lang: str,
    limit: float | int,
    include_status_report: bool,
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    Search for files in a project.

    Args:
        project: The name of the project to search for files in.
        lang: The language to search for files in.
        limit: The maximum number of files to return.
        include_status_report: Whether to include the status report in the response.
        toolCallId: The ID of the tool call.

    Returns:
        A dictionary containing the search results.

    Raises:
        Exception: If the files cannot be searched for.
    """
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
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    List missing files in a project.

    Args:
        project: The name of the project to list missing files in.
        lang: The language to list missing files in.
        limit: The maximum number of files to return.
        toolCallId: The ID of the tool call.
    
    Returns:
        A dictionary containing the list of missing files.

    Raises:
        Exception: If the missing files cannot be listed.
    """
    return build_missing_list_response(
        project=project,
        lang=lang,
        limit=int(limit or 1),
    )


def list_outdated_files(
    project: str,
    lang: str,
    limit: float | int,
    toolCallId: str = "",
) -> Dict[str, Any]:
    """
    List outdated files in a project.

    Args:
        project: The name of the project to list outdated files in.
        lang: The language to list outdated files in.
        limit: The maximum number of files to return.
        toolCallId: The ID of the tool call.
    
    Returns:
        A dictionary containing the list of outdated files.

    Raises:
        Exception: If the outdated files cannot be listed.
    """
    return build_outdated_list_response(
        project=project,
        lang=lang,
        limit=int(limit or 1),
    )
