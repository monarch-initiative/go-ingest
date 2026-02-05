# go-ingest

Koza ingest for Gene Ontology annotation data, transforming GAF files into Biolink model format.

## Data Source

[Gene Ontology](http://geneontology.org/) provides annotations linking genes to GO terms describing molecular functions, biological processes, and cellular components.

Data is downloaded from: `http://current.geneontology.org/annotations/`

### Species Included

- Human (9606)
- Mouse (10090)
- Rat (10116)
- Dog (9615)
- Pig (9823)
- Cow (9913)
- Chicken (9031)
- Zebrafish (7955)
- Fruit fly (7227)
- Baker's yeast (4932)
- Fission yeast (4896)
- C. elegans (6239)
- Dictyostelium (44689)

## Output

This ingest produces gene-to-GO term associations:
- **Molecular Activity** (Aspect F) - MacromolecularMachineToMolecularActivityAssociation
- **Biological Process** (Aspect P) - MacromolecularMachineToBiologicalProcessAssociation
- **Cellular Component** (Aspect C) - MacromolecularMachineToCellularComponentAssociation

## Usage

```bash
# Install dependencies
just install

# Run full pipeline
just run

# Or run steps individually
just download      # Download GO annotation GAF files
just transform-all # Run Koza transform
just test          # Run tests
```

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- [just](https://github.com/casey/just) command runner

## Citation

Ashburner et al. Gene ontology: tool for the unification of biology. Nat Genet. 2000 May;25(1):25-9. The Gene Ontology Consortium. The Gene Ontology knowledgebase in 2023. Genetics. 2023 May 4;224(1):iyad031

## License

MIT
