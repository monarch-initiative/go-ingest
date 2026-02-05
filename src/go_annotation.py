"""
Gene Ontology Annotations Ingest module.

Gene to GO term Associations
(to MolecularActivity, BiologicalProcess and CellularComponent)
"""

import sys
from pathlib import Path

# Add the src directory to sys.path for relative imports
_src_dir = Path(__file__).parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import uuid
import koza
from biolink_model.datamodel.pydanticmodel_v2 import KnowledgeLevelEnum, AgentTypeEnum

from loguru import logger
from annotation_utils import (
    parse_identifiers,
    go_aspect_to_biolink_class,
    biolink_predicate_map,
    aspect_map,
    relevant_aspects,
    default_no_evidence_found,
    qualifier_map,
)


@koza.transform_record()
def transform_record(koza_transform, row):
    """Transform a GO annotation row into an association."""
    # Grab relevant gene info and
    # Discern GO identifier 'Aspect' this term belongs to:
    #      'F' == molecular_function - child of GO:0003674
    #      'P' == biological_process - child of GO:0008150
    #      'C' == cellular_component - child of GO:0005575
    gene_id, ncbitaxa = parse_identifiers(row)
    go_id = row["GO_ID"]
    go_aspect = row["Aspect"].upper()
    evidence_code = row["Evidence_Code"]
    eco_term = None

    # Association predicate is normally NOT negated
    # except as noted below in the GAF qualifier field
    negated = False
    predicate = None

    # Deal with case where we can't make proper association
    if (not go_aspect) or (go_aspect not in relevant_aspects):
        logger.warning("GAF Aspec {} is empty or unrecongnized? Skipping reocrd...".format(go_aspect))
        return []

    # Lookup eco evidence code using koza map
    # koza_transform.lookup() returns the key if not found
    if evidence_code:
        eco_term = koza_transform.lookup(evidence_code, "eco_term", map_name="gaf_eco")
        if eco_term == evidence_code:  # lookup returns key if not found
            logger.warning("GAF Evidence Code {} is empty or unrecognized? Tagging as 'ND'".format(evidence_code))
            eco_term = default_no_evidence_found
    else:
        logger.warning("GAF Evidence Code is empty? Tagging as 'ND'")
        eco_term = default_no_evidence_found

    # The Association Predicate is otherwise inferred from the GAF 'Qualifier' used.
    # Note that this qualifier may be negated (i.e. "NOT|<qualifier>").
    key = tuple((go_id, eco_term))
    qualifier = qualifier_map.get(key, row["Qualifier"])

    # If qualifier missing, assign a default predicate
    # a.k.a. predicate based on specified GO Aspect type
    if not qualifier:
        logger.error("GAF record is missing its qualifier...assigning default qualifier as per GO term Aspect")
        predicate = aspect_map[go_aspect]

    else:
        # check for piped negation prefix (hopefully, well behaved!)
        qualifier_parts = qualifier.split("|")
        if qualifier_parts[0] == "NOT":
            predicate = biolink_predicate_map[qualifier_parts[1]]
            negated = True
        else:
            predicate = biolink_predicate_map[qualifier_parts[0]]

    # Can't make association with no predicate
    if not predicate:
        logger.error("GAF Qualifier {} is unrecognized? Skipping the record...".format(qualifier))
        return []

    # Primary knowledge source from GOA is in the "Assigned_By" column. Needs formatting
    assigned_by = "infores:{}".format(row["Assigned_By"].strip().lower().replace("_", "-"))

    # Format our publications ("Removes issues where prefix is duplicated for all DB_Reference
    # MGI:MGI:1234 --> MGI:1234
    publications = (
        [":".join(p.split(":")[::-1][0:2][::-1]) for p in row["DB_Reference"].split("|")] if row["DB_Reference"] else []
    )

    # Retrieve the GO aspect related NamedThing category-associated 'node' and Association 'edge' classes
    go_concept_node_class, gene_go_term_association_class = go_aspect_to_biolink_class[go_aspect]

    # Instantiate the appropriate Gene-to-GO Term instance
    association = gene_go_term_association_class(
        id="uuid:" + str(uuid.uuid1()),
        subject=gene_id,
        object=go_id,
        predicate=predicate,
        negated=negated,
        has_evidence=[eco_term],
        publications=publications,
        aggregator_knowledge_source=["infores:monarchinitiative"],
        primary_knowledge_source=assigned_by,
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_agent,
        species_context_qualifier=ncbitaxa,
    )
    # Return the captured Association
    return [association]
