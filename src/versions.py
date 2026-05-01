"""Upstream source version fetcher for go-ingest.

Two logical sources:
  - infores:goa — the per-species GAF files share a GO release, version
    is read from `!date-generated:` in any GAF file's header.
  - infores:eco — the gaf-eco-mapping comes from a github master branch
    (no formal release), version is the latest commit SHA.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kozahub_metadata_schema import (
    now_iso,
    urls_from_download_yaml,
    version_from_file_header,
    version_from_github_branch,
)


INGEST_DIR = Path(__file__).resolve().parents[1]
DOWNLOAD_YAML = INGEST_DIR / "download.yaml"
DATA_DIR = INGEST_DIR / "data"


def get_source_versions() -> list[dict[str, Any]]:
    goa_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["geneontology.org/annotations"])
    eco_urls = urls_from_download_yaml(DOWNLOAD_YAML, contains=["evidenceontology"])
    now = now_iso()

    sources: list[dict[str, Any]] = []

    if goa_urls:
        sample_gaf = next(DATA_DIR.glob("*.go_annotations.gaf.gz"), None)
        if sample_gaf is not None:
            ver, method = version_from_file_header(
                sample_gaf, pattern=r"!date-generated:\s*(\S+)"
            )
            ver = ver.split("T")[0] if "T" in ver else ver
        else:
            ver, method = "unknown", "unavailable"
        sources.append({
            "id": "infores:goa",
            "name": "GO Annotations (GOA)",
            "urls": goa_urls,
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        })

    if eco_urls:
        ver, method = version_from_github_branch("evidenceontology/evidenceontology", branch="master")
        sources.append({
            "id": "infores:eco",
            "name": "Evidence & Conclusion Ontology (gaf-eco-mapping)",
            "urls": eco_urls,
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        })

    return sources
