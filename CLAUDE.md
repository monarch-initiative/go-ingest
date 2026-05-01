# go-ingest

This is a Koza ingest repository for transforming Gene Ontology annotation data into Biolink model format.

## Project Structure

- `download.yaml` - Configuration for downloading GO annotation GAF files
- `src/` - Transform code and configuration
  - `go_annotation.py` / `go_annotation.yaml` - Main transform for GO annotations
  - `annotation_utils.py` - Utility functions for parsing GO annotation data
  - `versions.py` - Per-ingest upstream version fetcher (consumed by `just metadata`)
- `scripts/` - Utility scripts (preprocessing, plus `write_metadata.py` which emits `output/release-metadata.yaml`)
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
  - `release-metadata.yaml` - Per-build manifest of upstream sources, versions, artifacts (kozahub-metadata-schema)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> transform)
- `just download` - Download GO annotation GAF files
- `just transform-all` - Run all transforms
- `just transform <name>` - Run specific transform
- `just metadata` - Emit `output/release-metadata.yaml`
- `just test` - Run tests

## Data Sources

GO annotations are downloaded from http://current.geneontology.org/annotations/ for multiple species including human, mouse, rat, zebrafish, fly, worm, and yeast.

## Release Metadata

Every kozahub ingest emits an `output/release-metadata.yaml` describing the upstream sources, their versions, the artifacts produced, and the versions of build-time tools. This file is the contract monarch-ingest reads to assemble the merged knowledge graph's release receipt.

`src/versions.py` is the only per-ingest piece — it implements `get_source_versions()` returning a list of SourceVersion dicts. The `kozahub_metadata_schema` package provides reusable fetchers for the common patterns (HTTP Last-Modified, GitHub releases, URL-path regex, file-header parsing). The boilerplate (transform-content hashing, tool versions, build_version composition, yaml emission) is handled by `scripts/write_metadata.py`.

The `kozahub-metadata-schema` repo is expected as a sibling checkout (path-dep). Switch to a git or PyPI dep once published.

## Output

This ingest produces gene-to-GO term associations:
- MacromolecularMachineToMolecularActivityAssociation (Aspect F)
- MacromolecularMachineToBiologicalProcessAssociation (Aspect P)
- MacromolecularMachineToCellularComponentAssociation (Aspect C)

## Skills

- `.claude/skills/create-koza-ingest.md` - Create new koza ingests
- `.claude/skills/update-template.md` - Update to latest template version
