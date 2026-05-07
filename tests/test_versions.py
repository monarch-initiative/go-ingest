"""Unit tests for src/versions.py — per-GAF nested SourceVersion emission.

These exercise the parsing path (download.yaml → per-file infores mapping →
GAF header date) without hitting the network or the AGR FMS API.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from src import versions


GAF_HEADER = """!gaf-version: 2.2
!
!generated-by: GOC
!
!date-generated: 2025-10-11T19:57
!
!Header from source association file:
!=================================
!
!generated-by: GOC
!
!date-generated: 2025-10-10T17:37
!
"""


def _write_gaf(path: Path, date_generated: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = GAF_HEADER.replace("2025-10-11T19:57", date_generated)
    with gzip.open(path, "wt") as f:
        f.write(header)
        f.write("UniProtKB\tP12345\tFOO\t\tGO:0008150\tPMID:1\tIEA\t\tP\tFoo\t\tprotein\ttaxon:9606\t20250101\tUniProt\t\t\n")


@pytest.fixture
def fake_ingest(tmp_path, monkeypatch):
    """Build a minimal ingest tree at tmp_path with a download.yaml and one GAF."""
    (tmp_path / "data").mkdir()
    (tmp_path / "download.yaml").write_text(
        "- url: http://current.geneontology.org/annotations/mgi.gaf.gz\n"
        "  local_name: data/10090.go_annotations.gaf.gz\n"
        "- url: http://current.geneontology.org/annotations/zfin.gaf.gz\n"
        "  local_name: data/7955.go_annotations.gaf.gz\n"
        "- url: http://current.geneontology.org/annotations/something_unknown.gaf.gz\n"
        "  local_name: data/unknown.go_annotations.gaf.gz\n"
    )
    _write_gaf(tmp_path / "data" / "10090.go_annotations.gaf.gz", "2025-10-11T19:57")
    _write_gaf(tmp_path / "data" / "7955.go_annotations.gaf.gz", "2025-09-30T08:00")

    monkeypatch.setattr(versions, "INGEST_DIR", tmp_path)
    monkeypatch.setattr(versions, "DOWNLOAD_YAML", tmp_path / "download.yaml")
    monkeypatch.setattr(versions, "DATA_DIR", tmp_path / "data")
    return tmp_path


def test_per_gaf_sources_reads_date_generated(fake_ingest):
    sources = versions._per_gaf_sources(now="2026-01-01T00:00:00Z")

    by_id = {s["id"]: s for s in sources}
    assert by_id["infores:mgi"]["version"] == "2025-10-11"
    assert by_id["infores:mgi"]["version_method"] == "file_header"
    assert by_id["infores:zfin"]["version"] == "2025-09-30"


def test_per_gaf_sources_maps_url_basename_to_infores(fake_ingest):
    sources = versions._per_gaf_sources(now="2026-01-01T00:00:00Z")

    ids = {s["id"] for s in sources}
    assert ids == {"infores:mgi", "infores:zfin"}
    mgi = next(s for s in sources if s["id"] == "infores:mgi")
    assert mgi["urls"] == ["http://current.geneontology.org/annotations/mgi.gaf.gz"]


def test_per_gaf_sources_skips_unknown_basenames(fake_ingest):
    sources = versions._per_gaf_sources(now="2026-01-01T00:00:00Z")

    assert all(s["id"] != "infores:something_unknown" for s in sources)


def test_per_gaf_sources_handles_missing_local_file(tmp_path, monkeypatch):
    """If the GAF wasn't downloaded, the entry still emits with unknown version."""
    (tmp_path / "data").mkdir()
    (tmp_path / "download.yaml").write_text(
        "- url: http://current.geneontology.org/annotations/mgi.gaf.gz\n"
        "  local_name: data/10090.go_annotations.gaf.gz\n"
    )
    monkeypatch.setattr(versions, "INGEST_DIR", tmp_path)
    monkeypatch.setattr(versions, "DOWNLOAD_YAML", tmp_path / "download.yaml")
    monkeypatch.setattr(versions, "DATA_DIR", tmp_path / "data")

    sources = versions._per_gaf_sources(now="2026-01-01T00:00:00Z")

    assert len(sources) == 1
    assert sources[0]["id"] == "infores:mgi"
    assert sources[0]["version"] == "unknown"
    assert sources[0]["version_method"] == "unavailable"


def test_gaf_infores_covers_all_download_yaml_entries():
    """Catch drift: every GAF in the real download.yaml must be in GAF_INFORES."""
    import yaml
    real_download = Path(__file__).resolve().parents[1] / "download.yaml"
    entries = yaml.safe_load(real_download.read_text()) or []
    gaf_basenames = [e["url"].rsplit("/", 1)[-1] for e in entries if e.get("url", "").endswith(".gaf.gz")]
    missing = [b for b in gaf_basenames if b not in versions.GAF_INFORES]
    assert not missing, f"download.yaml has GAFs not mapped in GAF_INFORES: {missing}"
