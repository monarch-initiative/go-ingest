"""
Some Gene Ontology Annotation ingest utility functions.
"""

from re import sub, IGNORECASE, compile, Pattern
from typing import Optional, Tuple, List, Dict

from loguru import logger
from biolink_model.datamodel.pydanticmodel_v2 import (BiologicalProcess,
                                                      CellularComponent,
                                                      MacromolecularMachineToBiologicalProcessAssociation,
                                                      MacromolecularMachineToCellularComponentAssociation,
                                                      MacromolecularMachineToMolecularActivityAssociation,
                                                      MolecularActivity)


# Genome sequenced model for
# Aspergillus nidulans FGSC A4  a.k.a. Emericella nidulans
# The proper CURIE prefix for this is not certain
_gene_identifier_map: Dict[str, Tuple[str, Pattern]] = {"NCBITaxon:227321": ('AspGD', compile(r"(?P<identifier>AN\d+)\|"))}

# Create biolink predicate map in three steps
# Define predicate terms
# Map each term to its corresponding biolink predicate (1:1 "biolink:mapping" for all except involved_in)
# Add exceptions to the rule where the term is not a 1:1 to biolink (Currently 1 exception "involved_in"--> "actively_involved_in")
predicate_terms = ["enables", 
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
                   "acts_upstream_of_or_within_negative_effect"]
biolink_predicate_map = {pterm:"biolink:{}".format(pterm) for pterm in predicate_terms}
biolink_predicate_map["involved_in"] = "biolink:actively_involved_in" # Our one exception to the rule where the term is not a 1:1 to biolink


### https://geneontology.org/docs/go-annotation-file-gaf-format-2.2/#aspect-column-9
### https://biolink.github.io/biolink-model/associations.html
                                    # Category,         # Association
go_aspect_to_biolink_class = {"F": (MolecularActivity, MacromolecularMachineToMolecularActivityAssociation),
                              "P": (BiologicalProcess, MacromolecularMachineToBiologicalProcessAssociation),
                              "C": (CellularComponent, MacromolecularMachineToCellularComponentAssociation)}



def get_gaf_eco_map(gaf_eco_path):
    """
    - We want to join the second column with the first if it is not set to 'Default' on a '-' character
    - For 'Default' values we simply drop it from the mapping name and only retain the first column
    - The last column the term we are mapping to in this file (i.e. ECO evidence codes)
    - Two example formats
      "IEA-GO_REF:0000023": "ECO:0000501"
      "IRD": "ECO:0000321",
    """
    gaf_eco_map = {}
    with open(gaf_eco_path, 'r') as infile:
        for line in infile:
            line = line.strip('\r').strip('\n')
            if line[0] != "#":
                cols = line.split('\t')
                if cols[1] != "Default":
                    key = "{}-{}".format(cols[0], cols[1])
                else:
                    key = cols[0]
                gaf_eco_map.update({key:cols[-1]})
    
    ##print("- Terms in map {}".format(len(gaf_eco_map)))
    return gaf_eco_map


def parse_ncbi_taxa(taxon: str) -> List[str]:
    ncbi_taxa = []
    if taxon:
        # in rare circumstances, multiple taxa may be given as a piped list...
        ncbi_taxa = ["NCBITaxon:{}".format(taxa.split(":")[-1]) for taxa in taxon.split("|")]

    return ncbi_taxa


def parse_identifiers(row: Dict):
    """
    This method uses specific fields of the GOA data entry
    to resolve both the gene identifier and the NCBI Taxon
    """
    db: str = row['DB']
    db_object_id: str = row['DB_Object_ID']

    # This check is to clean up id's like MGI:MGI:123
    if ":" in db_object_id:
        db_object_id = db_object_id.split(':')[-1]

    ncbitaxa: List[str] = parse_ncbi_taxa(row['Taxon'])
    if not ncbitaxa:
        # Unlikely to happen, but...
        logger.warning(f"Missing taxa for '{db}:{db_object_id}'?")

    # Hacky remapping of some gene identifiers
    if ncbitaxa[0] in _gene_identifier_map.keys():
        id_regex: Pattern = _gene_identifier_map[ncbitaxa[0]][1]
        aliases: str = row['DB_Object_Synonym']
        match = id_regex.match(aliases)
        if match is not None:
            # Overwrite the 'db' and 'db_object_id' accordingly
            db = _gene_identifier_map[ncbitaxa[0]][0]
            db_object_id = match.group('identifier')

    gene_id: str = f"{db}:{db_object_id}"

    return gene_id, ncbitaxa
