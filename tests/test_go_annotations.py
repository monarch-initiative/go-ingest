"""
Unit tests for GO Annotations ingest

Uses Koza 2.x KozaTransform pattern with PassthroughWriter and mappings.
"""

import importlib.util
from pathlib import Path
from typing import Tuple

import pytest
import yaml
from biolink_model.datamodel.pydanticmodel_v2 import Association
from koza import KozaTransform
from koza.io.writer.passthrough_writer import PassthroughWriter
from koza.runner import load_transform
from loguru import logger

from annotation_utils import parse_identifiers

# Define the transform script path
TRANSFORM_SCRIPT = Path(__file__).parent.parent / "src" / "go_annotation.py"
TRANSFORM_CONFIG = Path(__file__).parent.parent / "src" / "go_annotation.yaml"


def load_module_from_path(path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_transform_with_mappings(rows: list[dict], mappings: dict[str, dict[str, dict[str, str]]]) -> list:
    """Run the transform on given rows with provided mappings and return entities."""
    module = load_module_from_path(TRANSFORM_SCRIPT)
    hooks = load_transform(module)
    writer = PassthroughWriter()

    hooks_obj = hooks.get(None)
    if hooks_obj is None:
        raise ValueError("No hooks found")

    koza_transform = KozaTransform(
        mappings=mappings,
        writer=writer,
        extra_fields={},
    )

    # Run the transform_record functions on each row
    for row in rows:
        for transform_fn in hooks_obj.transform_record:
            result = transform_fn(koza_transform, row)
            if result is not None:
                writer.write(result)

    writer.finalize()
    return writer.data


@pytest.fixture
def mappings():
    """
    Provide test mapping data in the format expected by KozaTransform.

    Format: {map_name: {key: {column: value}}}

    This fixture contains the ECO evidence code mappings used by the transform.
    """
    return {
        "gaf_eco": {
            # Standard evidence codes
            "EXP": {"eco_term": "ECO:0000269"},
            "HDA": {"eco_term": "ECO:0007005"},
            "HEP": {"eco_term": "ECO:0007007"},
            "HGI": {"eco_term": "ECO:0007003"},
            "HMP": {"eco_term": "ECO:0007001"},
            "HTP": {"eco_term": "ECO:0006056"},
            "IBA": {"eco_term": "ECO:0000318"},
            "IBD": {"eco_term": "ECO:0000319"},
            "IC": {"eco_term": "ECO:0000305"},
            "IDA": {"eco_term": "ECO:0000314"},
            "IEA": {"eco_term": "ECO:0000501"},
            "IEP": {"eco_term": "ECO:0000270"},
            "IGC": {"eco_term": "ECO:0000317"},
            "IGI": {"eco_term": "ECO:0000316"},
            "IKR": {"eco_term": "ECO:0000320"},
            "IMP": {"eco_term": "ECO:0000315"},
            "IPI": {"eco_term": "ECO:0000353"},
            "IRD": {"eco_term": "ECO:0000321"},
            "ISA": {"eco_term": "ECO:0000247"},
            "ISM": {"eco_term": "ECO:0000255"},
            "ISO": {"eco_term": "ECO:0000266"},
            "ISS": {"eco_term": "ECO:0000250"},
            "NAS": {"eco_term": "ECO:0000303"},
            "ND": {"eco_term": "ECO:0000307"},
            "RCA": {"eco_term": "ECO:0000245"},
            "TAS": {"eco_term": "ECO:0000304"},
        }
    }


@pytest.mark.parametrize(
    "query",
    [
        (
            {
                "DB": "AspGD",
                "DB_Object_ID": "ASPL0000057967",
                "DB_Object_Symbol": "catB",
                "Qualifier": "acts_upstream_of_or_within",
                "GO_ID": "GO:0019521",  # D-gluconate metabolic process
                "DB_Reference": "AspGD_REF:ASPL0000080002|PMID:18405346",
                "Evidence_Code": "RCA",
                "With_or_From": "",
                "Aspect": "P",
                "DB_Object_Name": "",
                "DB_Object_Synonym": "AN9339|ANID_09339|ANIA_09339",
                "DB_Object_Type": "gene_product",
                "Taxon": "taxon:227321",
                "Date": "20090403",
                "Assigned_By": "AspGD",
                "Annotation_Extension": "",
                "Gene_Product_Form_ID": "",
            },
            "AspGD:AN9339",
            "NCBITaxon:227321",
        )
    ],
)
def test_parse_identifiers(query: Tuple):
    gene_id, ncbitaxa = parse_identifiers(query[0])
    assert gene_id == query[1]
    assert query[2] in ncbitaxa


@pytest.fixture
def test_rows():
    """
    :return: List of test GO Annotation data rows (realistic looking but synthetic data).
    """
    return [  # Core data test: a completely normal record
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG1",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "enables",
            "GO_ID": "GO:0003723",  # molecular_function: RNA binding
            "DB_Reference": "GO_REF:0000043",
            "Evidence_Code": "IEA",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "F",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:9606",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Multiple taxa
        {
            "DB": "WB",
            "DB_Object_ID": "WBGene00000013",
            "DB_Object_Symbol": "abf-2",
            "Qualifier": "involved_in",
            "GO_ID": "GO:0050830",
            "DB_Reference": "WB_REF:WBPaper00045314|PMID:24882217",
            "Evidence_Code": "IEP",
            "With_or_From": "",
            "Aspect": "P",
            "DB_Object_Name": "",
            "DB_Object_Synonym": "C50F2.10|C50F2.e",
            "DB_Object_Type": "gene",
            "Taxon": "taxon:6239|taxon:46170",
            "Date": "20140827",
            "Assigned_By": "WB",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test default qualifier override for molecular function
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG2",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "contributes_to",
            "GO_ID": "GO:0003674",  # molecular_function root
            "DB_Reference": "GO_REF:0003674",
            "Evidence_Code": "ND",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "F",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:9606",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test default qualifier override for biological process
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG3",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "acts_upstream_of_negative_effect",
            "GO_ID": "GO:0008150",  # biological_process
            "DB_Reference": "GO_REF:0008150",
            "Evidence_Code": "ND",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "P",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:4932",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test default qualifier override for cellular compartment
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG4",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "colocalizes_with",
            "GO_ID": "GO:0005575",  # cellular compartment
            "DB_Reference": "GO_REF:0005575",
            "Evidence_Code": "ND",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "C",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:4932",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test non-default Biological Process and non-default qualifier
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "Q6GZX3",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "acts_upstream_of_or_within",
            "GO_ID": "GO:0045759",
            "DB_Reference": "GO_REF:0045759",
            "Evidence_Code": "ND",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "P",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:1000",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test outcome of unknown UniProt idmapping: uniprot id
        # is returned as gene id? Also try another evidence code
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG5",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "enables",
            "GO_ID": "GO:0003723",  # molecular_function: RNA binding
            "DB_Reference": "GO_REF:0000043",
            "Evidence_Code": "HMP",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "F",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:9606",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Test non-default Biological Process with negated qualifier
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "Q6GZX0",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "NOT|acts_upstream_of_or_within",
            "GO_ID": "GO:0045759",
            "DB_Reference": "GO_REF:0045759",
            "Evidence_Code": "ND",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "P",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:1000",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Missing (or wrong) GO term Aspect value - the record will be skipped?
        # So no entry is needed in the result_expected dictionary below
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "Q6GZX0",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "acts_upstream_of_or_within",
            "GO_ID": "GO:0045759",
            "DB_Reference": "GO_REF:0045759",
            "Evidence_Code": "IEA",
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:1000",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Missing (empty) qualifier - assign GO Aspect associated default
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG8",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "",
            "GO_ID": "GO:0005575",  # cellular compartment
            "DB_Reference": "GO_REF:0005575",
            "Evidence_Code": "IEA",  # Use a simple evidence code for this test
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "C",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:4932",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
        # Invalid Evidence Code - coerced into 'ND' -> "ECO:0000307"
        {
            "DB": "UniProtKB",
            "DB_Object_ID": "A0A024RBG9",
            "DB_Object_Symbol": "NUDT4B",
            "Qualifier": "enables",
            "GO_ID": "GO:0003723",
            "DB_Reference": "GO_REF:0000043",
            "Evidence_Code": "XXX",  # invalid Evidence Code
            "With_or_From": "UniProtKB-KW:KW-0694",
            "Aspect": "F",
            "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
            "DB_Object_Synonym": "NUDT4B",
            "DB_Object_Type": "protein",
            "Taxon": "taxon:9606",
            "Date": "20211010",
            "Assigned_By": "UniProt",
            "Annotation_Extension": "",
            "Gene_Product_Form_ID": "",
        },
    ]


#################################
### Expected results dictionary ###

result_expected = {  # Test regular MolecularActivity go term
    "UniProtKB:A0A024RBG1": [
        "biolink:Gene",
        "NCBITaxon:9606",
        "GO:0003723",
        "biolink:MolecularActivity",
        "biolink:BiologicalProcessOrActivity",
        "biolink:enables",
        "RO:0002327",
        False,
        "ECO:0000501",
    ],
    # Multiple Taxa
    "WB:WBGene00000013": [
        "biolink:Gene",
        ### Two are originally present in the input (6239, 46170)
        ### We want to take the FIRST one the is reported from left to right (taxon:6239|taxon:46170)
        "NCBITaxon:6239",
        "GO:0050830",
        "biolink:BiologicalProcess",
        "biolink:BiologicalProcessOrActivity",
        "biolink:actively_involved_in",
        "RO:0002331",
        False,
        "ECO:0000270",
    ],
    # Test default qualifier override for Molecular Activity go term
    "UniProtKB:A0A024RBG2": [
        "biolink:Gene",
        "NCBITaxon:9606",
        "GO:0003674",
        "biolink:MolecularActivity",
        "biolink:BiologicalProcessOrActivity",
        "biolink:enables",
        "RO:0002327",
        False,
        "ECO:0000307",
    ],
    # Test default qualifier override for Biological Process go term
    "UniProtKB:A0A024RBG3": [
        "biolink:Gene",
        "NCBITaxon:4932",
        "GO:0008150",
        "biolink:BiologicalProcess",
        "biolink:BiologicalProcessOrActivity",
        "biolink:actively_involved_in",
        "RO:0002331",
        False,
        "ECO:0000307",
    ],
    # Test default qualifier override for Cellular Component go term
    "UniProtKB:A0A024RBG4": [
        "biolink:Gene",
        "NCBITaxon:4932",
        "GO:0005575",
        "biolink:CellularComponent",
        "biolink:AnatomicalEntity",
        "biolink:active_in",
        "RO:0002432",
        False,
        "ECO:0000307",
    ],
    # Test non-default Biological Process and non-default qualifier
    "UniProtKB:Q6GZX3": [
        "biolink:Gene",
        "NCBITaxon:1000",
        "GO:0045759",
        "biolink:BiologicalProcess",
        "biolink:BiologicalProcessOrActivity",
        "biolink:acts_upstream_of_or_within",
        "RO:0002264",
        False,
        "ECO:0000307",
    ],
    # Test outcome of unknown UniProt idmapping: uniprot id
    # is returned as gene id? Also try another evidence code
    "UniProtKB:A0A024RBG5": [
        "biolink:Gene",
        "NCBITaxon:9606",
        "GO:0003723",
        "biolink:MolecularActivity",
        "biolink:BiologicalProcessOrActivity",
        "biolink:enables",
        "RO:0002327",
        False,
        "ECO:0007001",
    ],
    # Test non-default Biological Process with negated qualifier
    "UniProtKB:Q6GZX0": [
        "biolink:Gene",
        "NCBITaxon:1000",
        "GO:0045759",
        "biolink:BiologicalProcess",
        "biolink:BiologicalProcessOrActivity",
        "biolink:acts_upstream_of_or_within",
        "RO:0002264",
        True,
        "ECO:0000307",
    ],
    # Missing (empty) qualifier - assign GO Aspect associated default
    "UniProtKB:A0A024RBG8": [
        "biolink:Gene",
        "NCBITaxon:4932",
        "GO:0005575",
        "biolink:CellularComponent",
        "biolink:AnatomicalEntity",
        "biolink:located_in",
        "RO:0002432",
        False,
        "ECO:0000501",
    ],
    # Invalid Evidence Code - coerced into 'ND' -> "ECO:0000307"
    "UniProtKB:A0A024RBG9": [
        "biolink:Gene",
        "NCBITaxon:9606",
        "GO:0003723",
        "biolink:MolecularActivity",
        "biolink:BiologicalProcessOrActivity",
        "biolink:enables",
        "RO:0002327",
        False,
        "ECO:0000307",
    ],
}


def test_association(test_rows, mappings):
    """Test that the transform produces the expected associations using koza lookups."""
    entities = run_transform_with_mappings(test_rows, mappings)

    if not len(entities):
        logger.warning("test_association() null test?")
        return

    # We expect 10 associations (11 rows - 1 skipped due to empty Aspect)
    assert len(entities) == 10

    # Every produced subject should be represented exactly once in result_expected
    produced_subjects = [association.subject for association in entities]
    assert len(produced_subjects) == len(set(produced_subjects)), "unexpected duplicate subjects"

    # Validate EVERY produced association, not just the first one. This guards
    # against predicate regressions (e.g. is_active_in vs. active_in) that would
    # otherwise slip through if only entities[0] were checked.
    for association in entities:
        assert association
        assert association.subject in result_expected, f"unexpected subject {association.subject}"
        expected = result_expected[association.subject]

        assert association.object == expected[2]
        assert association.predicate == expected[5]
        assert association.negated == expected[7]
        assert expected[8] in association.has_evidence
        assert "infores:monarchinitiative" in association.aggregator_knowledge_source

    # Primary knowledge source is derived from the row's Assigned_By column;
    # the first fixture row is assigned by UniProt.
    assert entities[0].primary_knowledge_source == "infores:uniprot"

    # Taxon testing (multiple and single taxon values)
    single_taxa_association = entities[0]
    multi_taxa_association = entities[1]
    assert single_taxa_association.species_context_qualifier == result_expected[single_taxa_association.subject][1]
    assert multi_taxa_association.species_context_qualifier == result_expected[multi_taxa_association.subject][1]


def test_mgi_curie(mappings):
    """Test MGI CURIE formatting."""
    row = {
        "DB": "MGI",
        "DB_Object_ID": "MGI:1918911",
        "DB_Object_Symbol": "0610005C13Rik",
        "Qualifier": "enables",
        "GO_ID": "GO:0003674",
        "DB_Reference": "MGI:MGI:2156816|GO_REF:0000015",
        "Evidence_Code": "ND",
        "With_or_From": "",
        "Aspect": "F",
        "DB_Object_Name": "RIKEN cDNA 0610005C13 gene",
        "DB_Object_Synonym": "",
        "DB_Object_Type": "gene",
        "Taxon": "taxon:10090",
        "Date": "20200917",
        "Assigned_By": "MGI",
        "Annotation_Extension": "",
        "Gene_Product_Form_ID": "",
    }

    entities = run_transform_with_mappings([row], mappings)
    association = [assoc for assoc in entities if isinstance(assoc, Association)][0]
    assert association
    assert association.subject == "MGI:1918911"
    assert association.publications == ["MGI:2156816", "GO_REF:0000015"]
    assert association.primary_knowledge_source == "infores:mgi"
    assert "infores:monarchinitiative" in association.aggregator_knowledge_source


def test_invalid_evidence_code(mappings):
    """Test that invalid evidence codes fall back to ND (ECO:0000307)."""
    row = {
        "DB": "UniProtKB",
        "DB_Object_ID": "TEST123",
        "DB_Object_Symbol": "TEST",
        "Qualifier": "enables",
        "GO_ID": "GO:0003723",
        "DB_Reference": "GO_REF:0000043",
        "Evidence_Code": "INVALID_CODE",  # Not in the map
        "With_or_From": "",
        "Aspect": "F",
        "DB_Object_Name": "Test protein",
        "DB_Object_Synonym": "",
        "DB_Object_Type": "protein",
        "Taxon": "taxon:9606",
        "Date": "20211010",
        "Assigned_By": "UniProt",
        "Annotation_Extension": "",
        "Gene_Product_Form_ID": "",
    }

    entities = run_transform_with_mappings([row], mappings)
    assert len(entities) == 1
    # Invalid evidence code should fall back to ND -> ECO:0000307
    assert "ECO:0000307" in entities[0].has_evidence


def test_taxon_filter_covers_both_prefixes():
    """GAF files mix ``taxon:`` and ``NCBITaxon:`` prefixes in the Taxon column,
    and the reader's ``in`` filter is an exact string match, so every taxon id
    must be listed under both prefixes.
    """
    config = yaml.safe_load(TRANSFORM_CONFIG.read_text())
    taxon_filter = next(
        f for f in config["reader"]["filters"] if f.get("column") == "Taxon"
    )
    values = set(taxon_filter["value"])

    lower = {v.split(":", 1)[1] for v in values if v.startswith("taxon:")}
    ncbi = {v.split(":", 1)[1] for v in values if v.startswith("NCBITaxon:")}

    assert lower, "expected legacy taxon: entries in the Taxon filter"
    assert lower == ncbi, (
        "Taxon filter must enumerate every taxon under both taxon: and "
        f"NCBITaxon: prefixes; missing NCBITaxon: for {sorted(lower - ncbi)}, "
        f"missing taxon: for {sorted(ncbi - lower)}"
    )


def _biolink_predicate_curies() -> set[str]:
    """Return the set of valid biolink predicate CURIEs from the installed biolink model.

    A predicate is any slot that is (transitively) ``is_a: related to``. We read
    the schema YAML bundled with the ``biolink_model`` package so the check tracks
    whatever biolink-model version this ingest depends on.
    """
    import importlib.util

    spec = importlib.util.find_spec("biolink_model")
    pkg_dir = Path(spec.submodule_search_locations[0])
    schema_path = pkg_dir / "schema" / "biolink_model.yaml"
    slots = yaml.safe_load(schema_path.read_text())["slots"]

    def is_predicate(name: str) -> bool:
        cur = name
        while cur:
            if cur == "related to":
                return True
            slot = slots.get(cur)
            cur = slot.get("is_a") if slot else None
        return False

    return {"biolink:" + name.replace(" ", "_") for name in slots if is_predicate(name)}


def test_only_real_biolink_predicates():
    """Every predicate the transform can emit must be a real biolink predicate.

    Guards monarch-app#1360: ``biolink:is_active_in`` is not a canonical biolink
    predicate (the slot is ``active_in`` / RO:0002432).
    """
    from annotation_utils import aspect_map, biolink_predicate_map, qualifier_map

    valid = _biolink_predicate_curies()
    # sanity: the canonical slot exists and the non-canonical one does not
    assert "biolink:active_in" in valid
    assert "biolink:is_active_in" not in valid

    # Collect every biolink predicate CURIE the transform can produce:
    emitted = set(biolink_predicate_map.values())
    # aspect_map defaults are routed through biolink_predicate_map at the use site
    emitted |= {biolink_predicate_map[term] for term in aspect_map.values()}
    # qualifier_map (ND root-node) defaults are likewise routed through biolink_predicate_map
    emitted |= {biolink_predicate_map[q] for q in qualifier_map.values()}

    invalid = sorted(p for p in emitted if p not in valid)
    assert not invalid, f"transform emits non-biolink predicate(s): {invalid}"


def test_empty_aspect_skipped(mappings):
    """Test that rows with empty Aspect are skipped."""
    row = {
        "DB": "UniProtKB",
        "DB_Object_ID": "TEST456",
        "DB_Object_Symbol": "TEST",
        "Qualifier": "enables",
        "GO_ID": "GO:0003723",
        "DB_Reference": "GO_REF:0000043",
        "Evidence_Code": "IEA",
        "With_or_From": "",
        "Aspect": "",  # Empty aspect
        "DB_Object_Name": "Test protein",
        "DB_Object_Synonym": "",
        "DB_Object_Type": "protein",
        "Taxon": "taxon:9606",
        "Date": "20211010",
        "Assigned_By": "UniProt",
        "Annotation_Extension": "",
        "Gene_Product_Form_ID": "",
    }

    entities = run_transform_with_mappings([row], mappings)
    assert len(entities) == 0
