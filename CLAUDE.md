# go-ingest

This is a Koza ingest repository for transforming Gene Ontology annotation data into Biolink model format.

## Project Structure

- `download.yaml` - Configuration for downloading GO annotation GAF files
- `src/` - Transform code and configuration
  - `go_annotation.py` / `go_annotation.yaml` - Main transform for GO annotations
  - `annotation_utils.py` - Utility functions for parsing GO annotation data
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> transform)
- `just download` - Download GO annotation GAF files
- `just transform-all` - Run all transforms
- `just test` - Run tests

## Data Sources

GO annotations are downloaded from http://current.geneontology.org/annotations/ for multiple species including human, mouse, rat, zebrafish, fly, worm, and yeast.

## Output

This ingest produces gene-to-GO term associations:
- MacromolecularMachineToMolecularActivityAssociation (Aspect F)
- MacromolecularMachineToBiologicalProcessAssociation (Aspect P)
- MacromolecularMachineToCellularComponentAssociation (Aspect C)
