"""Upstream source version fetcher for go-ingest.

Top-level sources:
  - infores:goa — the per-species GAF files share a GO release; bundle
    version is the `!date-generated:` of any GAF.
  - infores:eco — the gaf-eco-mapping comes from a github master branch
    (no formal release), version is the latest commit SHA.

Nested under infores:goa, one SourceVersion per consumed GAF file records
the per-species `!date-generated:` from that file's header. Edges in this
ingest's output carry per-source `primary_knowledge_source` (derived from
the GAF `Assigned_By` column in src/go_annotation.py), so a downstream
consumer (e.g. monarch-app) can resolve an edge's exact upstream version
even though everything was retrieved via GO/GOA.

Per-file infores choices: the model-organism GAFs (mgi, rgd, zfin, fb, wb,
sgd, pombase, dictybase) map straightforwardly to their MOD's infores. The
`goa_*` files are UniProt-mediated species-specific submissions; they map
to infores:goa-{species} rather than infores:uniprot, mirroring the GO
project's own labeling (see Header from goa_{species} source association
file in each GAF).
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

# Map from upstream GAF basename -> (infores, human-readable name).
# Keyed by the basename in the GO download URL (not our local taxid name).
GAF_INFORES = {
    "mgi.gaf.gz": ("infores:mgi", "Mouse Genome Informatics"),
    "rgd.gaf.gz": ("infores:rgd", "Rat Genome Database"),
    "zfin.gaf.gz": ("infores:zfin", "ZFIN"),
    "fb.gaf.gz": ("infores:flybase", "FlyBase"),
    "wb.gaf.gz": ("infores:wormbase", "WormBase"),
    "sgd.gaf.gz": ("infores:sgd", "Saccharomyces Genome Database"),
    "pombase.gaf.gz": ("infores:pombase", "PomBase"),
    "dictybase.gaf.gz": ("infores:dictybase", "dictyBase"),
    "goa_human.gaf.gz": ("infores:goa-human", "GOA Human (UniProt)"),
    "goa_dog.gaf.gz": ("infores:goa-dog", "GOA Dog (UniProt)"),
    "goa_cow.gaf.gz": ("infores:goa-cow", "GOA Cow (UniProt)"),
    "goa_pig.gaf.gz": ("infores:goa-pig", "GOA Pig (UniProt)"),
    "goa_chicken.gaf.gz": ("infores:goa-chicken", "GOA Chicken (UniProt)"),
}


def _per_gaf_sources(now: str) -> list[dict[str, Any]]:
    """Build nested SourceVersion entries, one per consumed GAF.

    Pairs each download.yaml entry's `url` (upstream basename) with its
    `local_name` (taxid path) by re-reading download.yaml. Falls back to
    skipping entries we don't recognize.
    """
    import yaml
    raw = yaml.safe_load(DOWNLOAD_YAML.read_text())
    entries = raw if isinstance(raw, list) else raw.get("downloads", [])

    sources: list[dict[str, Any]] = []
    for e in entries or []:
        url = e.get("url", "")
        local = e.get("local_name", "")
        basename = url.rsplit("/", 1)[-1]
        if basename not in GAF_INFORES:
            continue
        infores, name = GAF_INFORES[basename]
        local_path = INGEST_DIR / local
        if local_path.is_file():
            ver, method = version_from_file_header(
                local_path, pattern=r"!date-generated:\s*(\S+)"
            )
            ver = ver.split("T")[0] if "T" in ver else ver
        else:
            ver, method = "unknown", "unavailable"
        sources.append({
            "id": infores,
            "name": name,
            "urls": [url],
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        })

    sources.sort(key=lambda s: s["id"])
    return sources


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
        entry: dict[str, Any] = {
            "id": "infores:goa",
            "name": "GO Annotations (GOA)",
            "urls": goa_urls,
            "version": ver,
            "version_method": method,
            "retrieved_at": now,
        }
        nested = _per_gaf_sources(now)
        if nested:
            entry["sources"] = nested
        sources.append(entry)

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
