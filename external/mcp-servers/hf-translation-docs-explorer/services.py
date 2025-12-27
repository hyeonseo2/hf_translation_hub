from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import git

from adapters import fetch_document_paths
from setting import SETTINGS


# ------------------------------
# Language choices (UI)
# ------------------------------
LANGUAGE_CHOICES: List[str] = ["ko", "ja", "zh", "fr", "de"]


# ------------------------------
# Project model
# ------------------------------
@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    repo_url: str
    docs_path: str
    tree_api_url: str

    @property
    def repo_path(self) -> str:
        return self.repo_url.replace("https://github.com/", "")


# ------------------------------
# Supported projects
# ------------------------------
PROJECTS: Dict[str, Project] = {
    "transformers": Project(
        slug="transformers",
        name="Transformers",
        repo_url="https://github.com/huggingface/transformers",
        docs_path="docs/source",
        tree_api_url="https://api.github.com/repos/huggingface/transformers/git/trees/main?recursive=1",
    ),
    "smolagents": Project(
        slug="smolagents",
        name="SmolAgents",
        repo_url="https://github.com/huggingface/smolagents",
        docs_path="docs/source",
        tree_api_url="https://api.github.com/repos/huggingface/smolagents/git/trees/main?recursive=1",
    ),
}


# ------------------------------
# Repo & result cache
# ------------------------------
REPO_BASE = Path("/data/repos")
CACHE_BASE = Path("/data/cache")
CACHE_BASE.mkdir(parents=True, exist_ok=True)


def _prepare_repo(project: Project) -> git.Repo:
    repo_dir = REPO_BASE / project.slug
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    if repo_dir.exists():
        repo = git.Repo(repo_dir)
        repo.git.fetch()
        repo.git.reset("--hard", "origin/main")
    else:
        repo = git.Repo.clone_from(project.repo_url, repo_dir)

    return repo


def _cache_path(project: str, lang: str) -> Path:
    return CACHE_BASE / f"{project}_{lang}_status.json"


def _load_cached_status(project: str, lang: str, head_sha: str):
    path = _cache_path(project, lang)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        if data.get("head_sha") == head_sha:
            return data["payload"]
    except Exception:
        return None

    return None


def _save_cached_status(
    project: str,
    lang: str,
    head_sha: str,
    payload: Dict[str, Any],
):
    path = _cache_path(project, lang)
    path.write_text(
        json.dumps(
            {
                "head_sha": head_sha,
                "payload": payload,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


# ------------------------------
# Helpers
# ------------------------------
def get_available_projects() -> List[str]:
    return sorted(PROJECTS.keys())


def _iter_english_docs(all_docs: Iterable[str], docs_root: str) -> Iterable[Path]:
    english_root = Path(docs_root) / "en"

    for doc_path in all_docs:
        if not doc_path.endswith(".md"):
            continue
        path = Path(doc_path)
        try:
            path.relative_to(english_root)
        except ValueError:
            continue
        yield path


def _last_commit(repo: git.Repo, repo_root: Path, file_path: Path):
    if not file_path.exists():
        return None
    rel = file_path.relative_to(repo_root)
    for c in repo.iter_commits(paths=str(rel), max_count=1):
        return c
    return None


def _last_content_change_commit(
    repo: git.Repo,
    repo_root: Path,
    file_path: Path,
    max_commits: int = 200,
):
    if not file_path.exists():
        return None

    rel = file_path.relative_to(repo_root)
    for c in repo.iter_commits(paths=str(rel), max_count=max_commits):
        stats = c.stats.files.get(str(rel))
        if stats and (stats.get("insertions", 0) > 0 or stats.get("deletions", 0) > 0):
            return c
    return None


# ------------------------------
# Core computation (cached)
# ------------------------------
def _compute_translation_status(
    project_key: str,
    language: str,
    limit: int,
) -> Tuple[str, List[Dict[str, Any]], Project]:
    project = PROJECTS[project_key]
    repo = _prepare_repo(project)
    repo_root = Path(repo.working_tree_dir)

    head_sha = repo.head.commit.hexsha

    cached = _load_cached_status(project_key, language, head_sha)
    if cached:
        status_report = cached["status_report"]
        all_items = cached["items"]
        candidates = [
            item for item in all_items
            if item["missing"] or item["outdated"]
        ][:limit]
        return status_report, candidates, project

    # -------- FULL SCAN (HEAD 변경 시에만 실행) --------
    all_paths = fetch_document_paths(project.tree_api_url)
    english_docs = list(_iter_english_docs(all_paths, project.docs_path))
    english_total = len(english_docs)
    docs_set = set(all_paths)

    missing_count = 0
    outdated_count = 0
    up_to_date_count = 0

    per_doc_status: List[Dict[str, Any]] = []

    for english_doc in english_docs:
        relative = english_doc.relative_to(Path(project.docs_path) / "en")
        translated_path = Path(project.docs_path) / language / relative

        en_file = repo_root / english_doc
        ko_file = repo_root / translated_path

        en_change = _last_content_change_commit(repo, repo_root, en_file)
        ko_commit = _last_commit(repo, repo_root, ko_file)

        missing = str(translated_path) not in docs_set
        outdated = False

        if missing:
            missing_count += 1
            status = "missing"
        else:
            if en_change and ko_commit and ko_commit.committed_datetime < en_change.committed_datetime:
                outdated = True
                outdated_count += 1
                status = "outdated"
            else:
                up_to_date_count += 1
                status = "up_to_date"

        per_doc_status.append(
            {
                "path": str(english_doc),
                "status": status,
                "missing": missing,
                "outdated": outdated,
                "en_latest_change": (
                    en_change.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    if en_change
                    else None
                ),
                "ko_base_commit": (
                    ko_commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    if ko_commit
                    else None
                ),
            }
        )

    translatable = english_total - missing_count
    coverage_pct = (
        (up_to_date_count / translatable * 100)
        if translatable > 0
        else 0.0
    )

    status_report = (
        "| Item | Count |\n"
        "|------|-------|\n"
        f"| English docs | {english_total} |\n"
        f"| Missing translations | {missing_count} |\n"
        f"| Translatable docs | {translatable} |\n"
        f"| Up-to-date translations | {up_to_date_count} |\n"
        f"| Outdated translations | {outdated_count} |\n\n"
        f"**Translation coverage (of translatable docs): {coverage_pct:.2f}%**"
    )

    payload = {
        "status_report": status_report,
        "items": per_doc_status,
    }

    _save_cached_status(
        project=project_key,
        lang=language,
        head_sha=head_sha,
        payload=payload,
    )

    candidates = [
        item for item in per_doc_status
        if item["missing"] or item["outdated"]
    ][:limit]

    return status_report, candidates, project


# ------------------------------
# Public builders
# ------------------------------
def build_project_catalog(default: str | None) -> Dict[str, Any]:
    slugs = get_available_projects()
    default = default if default in slugs else None

    return {
        "type": "translation.project_list",
        "projects": [
            {
                "slug": slug,
                "display_name": PROJECTS[slug].name,
                "repo_url": PROJECTS[slug].repo_url,
                "docs_path": PROJECTS[slug].docs_path,
            }
            for slug in slugs
        ],
        "default_project": default,
        "total_projects": len(slugs),
    }


def build_search_response(
    project: str,
    lang: str,
    limit: int,
    include_status_report: bool,
) -> Dict[str, Any]:
    status_report, items, project_cfg = _compute_translation_status(
        project_key=project,
        language=lang,
        limit=limit,
    )

    repo_url = project_cfg.repo_url.rstrip("/")

    return {
        "type": "translation.search.response",
        "files": [
            {
                "rank": idx,
                "path": item["path"],
                "repo_url": f"{repo_url}/blob/main/{item['path']}",
                "metadata": item,
            }
            for idx, item in enumerate(items, start=1)
        ],
        "total_candidates": len(items),
        "status_report": status_report if include_status_report else None,
    }


def build_missing_list_response(
    project: str,
    lang: str,
    limit: int,
) -> Dict[str, Any]:
    status_report, items, project_cfg = _compute_translation_status(
        project_key=project,
        language=lang,
        limit=limit,
    )

    repo_url = project_cfg.repo_url.rstrip("/")
    missing_items = [i for i in items if i["missing"]]

    return {
        "type": "translation.missing_list",
        "project": project,
        "target_language": lang,
        "count": len(missing_items),
        "files": [
            {
                "rank": idx,
                "path": item["path"],
                "repo_url": f"{repo_url}/blob/main/{item['path']}",
                "metadata": item,
            }
            for idx, item in enumerate(missing_items, start=1)
        ],
        "status_report": status_report,
    }


def build_outdated_list_response(
    project: str,
    lang: str,
    limit: int,
) -> Dict[str, Any]:
    status_report, items, project_cfg = _compute_translation_status(
        project_key=project,
        language=lang,
        limit=limit,
    )

    repo_url = project_cfg.repo_url.rstrip("/")
    outdated_items = [i for i in items if i["outdated"]]

    return {
        "type": "translation.outdated_list",
        "project": project,
        "target_language": lang,
        "count": len(outdated_items),
        "files": [
            {
                "rank": idx,
                "path": item["path"],
                "repo_url": f"{repo_url}/blob/main/{item['path']}",
                "metadata": item,
            }
            for idx, item in enumerate(outdated_items, start=1)
        ],
        "status_report": status_report,
    }
