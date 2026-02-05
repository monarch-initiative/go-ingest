"""
Some Gene Ontology Annotation ingest utility functions.
"""

from re import sub, IGNORECASE, compile, Pattern
from typing import Optional, Tuple, List, Dict

from loguru import logger
from biolink_model.datamodel.pydanticmodel_v2 import (
    BiologicalProcess,
    CellularComponent,
    MacromolecularMachineToBiologicalProcessAssociation,
    MacromolecularMachineToCellularComponentAssociation,
    MacromolecularMachineToMolecularActivityAssociation,
    MolecularActivity,
)


# The three values allowed in the "Aspect" column of the gaf files for this ingest
# https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#db-column-9
aspect_map = {"F": "enables", "P": "involved_in", "C": "located_in"}
relevant_aspects = set(list(aspect_map.keys()))
default_no_evidence_found = "ECO:0000307"  # https://www.ebi.ac.uk/QuickGO/term/ECO:0000307


# For root node annotations that use the ND evidence code should be used:
#     molecular_function (GO:0003674) enables (RO:0002327)
#     biological_process (GO:0008150) involved_in (RO:0002331)
#     cellular_component (GO:0005575) is_active_in (RO:0002432)
qualifier_map = {
    tuple(
        ("GO:0003674", "ECO:0000307")
    ): "enables",  # https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#db-column-4
    tuple(("GO:0008150", "ECO:0000307")): "involved_in",
    tuple(("GO:0005575", "ECO:0000307")): "is_active_in",
}


# Genome sequenced model for
# Aspergillus nidulans FGSC A4  a.k.a. Emericella nidulans
# The proper CURIE prefix for this is not certain
_gene_identifier_map: Dict[str, Tuple[str, Pattern]] = {
    "NCBITaxon:227321": ("AspGD", compile(r"(?P<identifier>AN\d+)\|"))
}


# Create biolink predicate map in three steps
# Define predicate terms
# Map each term to its corresponding biolink predicate (1:1 "biolink:mapping" for all except involved_in)
# Add exceptions to the rule where the term is not a 1:1 to biolink (Currently 1 exception "involved_in"--> "actively_involved_in")
predicate_terms = [
    "enables",
    "involved_in",
    "located_in",
    "contributes_to",
    "acts_upstream_of",
    "part_of",
    "is_active_in",
    "colocalizes_with",
    "acts_upstream_of_or_within",
    "acts_upstream_of_positive_effect",
    "acts_upstream_of_negative_effect",
    "acts_upstream_of_or_within_positive_effect",
    "acts_upstream_of_or_within_negative_effect",
]
biolink_predicate_map = {pterm: "biolink:{}".format(pterm) for pterm in predicate_terms}
biolink_predicate_map["involved_in"] = (
    "biolink:actively_involved_in"  # Our one exception to the rule where the term is not a 1:1 to biolink
)


### https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#aspect-column-9
### https://biolink.github.io/biolink-model/associations.html
# Category,         # Association
go_aspect_to_biolink_class = {
    "F": (MolecularActivity, MacromolecularMachineToMolecularActivityAssociation),
    "P": (BiologicalProcess, MacromolecularMachineToBiologicalProcessAssociation),
    "C": (CellularComponent, MacromolecularMachineToCellularComponentAssociation),
}


def parse_ncbi_taxa(taxon: str) -> List[str]:
    ncbi_taxa = []
    if taxon:
        # in rare circumstances, multiple taxa may be given as a piped list...(Human 9606 this occurs for example)
        ncbi_taxa = ["NCBITaxon:{}".format(taxa.split(":")[-1]) for taxa in taxon.split("|")]

    # TO DO: Do we want to include the other taxon?
    # These include things like retro viruses. For example, https://www.ncbi.nlm.nih.gov/taxonomy/?term=11746
    # By default, we return the first taxon listed, which corresponds to the annotation in question
    return ncbi_taxa


def parse_identifiers(row: Dict):
    """
    This method uses specific fields of the GOA data entry
    to resolve both the gene identifier and the NCBI Taxon
    """
    db: str = row["DB"]
    db_object_id: str = row["DB_Object_ID"]

    # This check is to clean up id's like MGI:MGI:123
    if ":" in db_object_id:
        db_object_id = db_object_id.split(":")[-1]

    ncbitaxa: List[str] = parse_ncbi_taxa(row["Taxon"])
    if not ncbitaxa:
        # Unlikely to happen, but...
        logger.warning(f"Missing taxa for '{db}:{db_object_id}'?")

    # Remapping of Aspergillus 227321 gene identifiers.
    # The annotations are not consistent in terms of which columns we can directly pull from for this taxon
    # Therefore, we must pull from the DB_Object_Synonym column to pull out the gene symbol in a consistent way
    if ncbitaxa[0] in _gene_identifier_map.keys():
        id_regex: Pattern = _gene_identifier_map[ncbitaxa[0]][1]
        aliases: str = row["DB_Object_Synonym"]
        match = id_regex.match(aliases)
        if match is not None:
            # Overwrite the 'db' and 'db_object_id' accordingly
            db = _gene_identifier_map[ncbitaxa[0]][0]
            db_object_id = match.group("identifier")

    gene_id: str = f"{db}:{db_object_id}"

    return gene_id, ncbitaxa[0]
