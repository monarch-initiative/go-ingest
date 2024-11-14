"""
Unit tests for GO Annotations ingest
"""

import pytest
import os
import sys
from typing import Tuple
from biolink_model.datamodel.pydanticmodel_v2 import Association
from koza.utils.testing_utils import mock_koza  # noqa: F401  # noqa: F401
from loguru import logger

# Grab parent directory as string, and then add where our ingest code is located, and lastly add to sytem path
parent_dir = '/'.join(os.path.dirname(__file__).split('/')[:-1])
ingest_code_dir = os.path.join(parent_dir, "src/go_ingest")
sys.path.append(ingest_code_dir)


# Now that our "system" path recognizes our src/ directory we can import our utils and constants
from annotation_utils import parse_identifiers, get_gaf_eco_map


@pytest.mark.parametrize("query", 
                        [({"DB": "AspGD",
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
                           "Gene_Product_Form_ID": ""}, 

                           "AspGD:AN9339",

                           "NCBITaxon:227321")]
                           )
def test_parse_identifiers(query: Tuple):
    gene_id, ncbitaxa = parse_identifiers(query[0])
    assert gene_id == query[1]
    assert query[2] in ncbitaxa


@pytest.fixture
def gaf_eco_path():
    """
    :return: string of path to gaf-eco-mappings.txt file
    """
    return "./data/gaf-eco-mapping.txt"
    #return os.path.join(ingest_data_dir, "gaf-eco-mapping.txt")


@pytest.fixture
def map_cache(gaf_eco_path):
    """
    Is meant to return a dictionary mapping evidence codes to ECO:000... (i.e. {"IGI":"ECO:0000316", ... })
    """
    return get_gaf_eco_map(gaf_eco_path)


@pytest.fixture
def source_name():
    """
    :return: string source name of GO Annotations ingest
    """
    return "go_annotation"


@pytest.fixture
def script():
    """
    :return: string path to GO Annotations ingest script
    """
    return "./src/go_ingest/annotation_transform.py"


@pytest.fixture
def test_rows():
    """
    :return: List of test GO Annotation data rows (realistic looking but synthetic data).
    """
    return [ # Core data test: a completely normal record
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},

            # Multiple taxa
            {"DB": "WB",
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
             "Gene_Product_Form_ID": ""},

            # Test default qualifier override for molecular function
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},

            # Test default qualifier override for biological process
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},
        
            # Test default qualifier override for cellular compartment
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},

            # Test non-default Biological Process and non-default qualifier
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},

            # Test outcome of unknown UniProt idmapping: uniprot id
            # is returned as gene id? Also try another evidence code
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},
        
            # Test non-default Biological Process with negated qualifier
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},
        
            # Missing (or wrong) GO term Aspect value - the record will be skipped?
            # So no entry is needed in the result_expected dictionary below
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""},
        
            # Missing (empty) qualifier - assign GO Aspect associated default
            {"DB": "UniProtKB",
             "DB_Object_ID": "A0A024RBG8",
             "DB_Object_Symbol": "NUDT4B",
             "Qualifier": "",
             "GO_ID": "GO:0005575",  # cellular compartment
             "DB_Reference": "GO_REF:0005575",
             "Evidence_Code": "IEA-GO_REF:0000041",
             "With_or_From": "UniProtKB-KW:KW-0694",
             "Aspect": "C",
             "DB_Object_Name": "Diphosphoinositol polyphosphate phosphohydrolase",
             "DB_Object_Synonym": "NUDT4B",
             "DB_Object_Type": "protein",
             "Taxon": "taxon:4932",
             "Date": "20211010",
             "Assigned_By": "UniProt",
             "Annotation_Extension": "",
             "Gene_Product_Form_ID": ""},

            # Invalid Evidence Code - coerced into 'ND' -> "ECO:0000307"
            {"DB": "UniProtKB",
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
             "Gene_Product_Form_ID": ""}]


@pytest.fixture
def basic_go(mock_koza, source_name, test_rows, script, map_cache):
    """
    Mock Koza run for GO annotation ingest.

    :param mock_koza:
    :param source_name:
    :param test_rows:
    :param script:
    :param local_table:

    :return: mock_koza application
    """
    return mock_koza(name=source_name,
                     data=test_rows,
                     transform_code=script,
                     map_cache=map_cache)


@pytest.fixture
def mgi_entities(mock_koza, source_name, script, map_cache):
    row = {"DB": "MGI",
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
           "Gene_Product_Form_ID": ""}

    return mock_koza(name=source_name,
                     data=row,
                     transform_code=script,
                     map_cache=map_cache)


#################################
### Run our (remaining) tests ###

result_expected = {# Test regular MolecularActivity go term
                   "UniProtKB:A0A024RBG1": ["biolink:Gene",
                                            "NCBITaxon:9606",
                                            "GO:0003723",
                                            "biolink:MolecularActivity",
                                            "biolink:BiologicalProcessOrActivity",
                                            "biolink:enables",
                                            "RO:0002327",
                                            False,
                                            "ECO:0000501"],

                    # Multiple Taxa
                    "WB:WBGene00000013": ["biolink:Gene",
                                          
                                          ### Two are originally present in the input (6239, 46170)
                                          ### We want to take the FIRST one the is reported from left to right (taxon:6239|taxon:46170)
                                          "NCBITaxon:6239",
                                          "GO:0050830",
                                          "biolink:BiologicalProcess",
                                          "biolink:BiologicalProcessOrActivity",
                                          "biolink:actively_involved_in",
                                          "RO:0002331",
                                          False,
                                          "ECO:0000270"],

                    # Test default qualifier override for Molecular Activity go term
                    "UniProtKB:A0A024RBG2": ["biolink:Gene",
                                             "NCBITaxon:9606",
                                             "GO:0003674",
                                             "biolink:MolecularActivity",
                                             "biolink:BiologicalProcessOrActivity",
                                             "biolink:enables",
                                             "RO:0002327",
                                             False,
                                             "ECO:0000307"],

                    # Test default qualifier override for Biological Process go term
                    "UniProtKB:A0A024RBG3": ["biolink:Gene",
                                             "NCBITaxon:4932",
                                             "GO:0008150",
                                             "biolink:BiologicalProcess",
                                             "biolink:BiologicalProcessOrActivity",
                                             "biolink:actively_involved_in",
                                             "RO:0002331",
                                             False,
                                             "ECO:0000307"],

                    # Test default qualifier override for Cellular Component go term
                    "UniProtKB:A0A024RBG4": ["biolink:Gene",
                                             "NCBITaxon:4932",
                                             "GO:0005575",
                                             "biolink:CellularComponent",
                                             "biolink:AnatomicalEntity",
                                             "biolink:active_in",
                                             "RO:0002432",
                                             False,
                                             "ECO:0000307"],

                    # Test non-default Biological Process and non-default qualifier
                    "UniProtKB:Q6GZX3": ["biolink:Gene",
                                         "NCBITaxon:1000",
                                         "GO:0045759",
                                         "biolink:BiologicalProcess",
                                         "biolink:BiologicalProcessOrActivity",
                                         "biolink:acts_upstream_of_or_within",
                                         "RO:0002264",
                                         False,
                                         "ECO:0000307"],

                    # Test outcome of unknown UniProt idmapping: uniprot id
                    # is returned as gene id? Also try another evidence code
                    "UniProtKB:A0A024RBG5": ["biolink:Gene",
                                             "NCBITaxon:9606",
                                             "GO:0003723",
                                             "biolink:MolecularActivity",
                                             "biolink:BiologicalProcessOrActivity",
                                             "biolink:enables",
                                             "RO:0002327",
                                             False,
                                             "ECO:0007001"],

                    # Test non-default Biological Process with negated qualifier
                    "UniProtKB:Q6GZX0": ["biolink:Gene",
                                         "NCBITaxon:1000",
                                         "GO:0045759",
                                         "biolink:BiologicalProcess",
                                         "biolink:BiologicalProcessOrActivity",
                                         "biolink:acts_upstream_of_or_within",
                                         "RO:0002264",
                                         True,
                                         "ECO:0000307"],

                    # Missing (empty) qualifier - assign GO Aspect associated default
                    "UniProtKB:A0A024RBG8": ["biolink:Gene",
                                             "NCBITaxon:4932",
                                             "GO:0005575",
                                             "biolink:CellularComponent",
                                             "biolink:AnatomicalEntity",
                                             "biolink:located_in",
                                             "RO:0002432",
                                             False,
                                             "ECO:0000307"],

                    # Invalid Evidence Code - coerced into 'ND' -> "ECO:0000307"
                    "UniProtKB:A0A024RBG9": ["biolink:Gene",
                                             "NCBITaxon:9606",
                                             "GO:0003723",
                                             "biolink:MolecularActivity",
                                             "biolink:BiologicalProcessOrActivity",
                                             "biolink:enables",
                                             "RO:0002327",
                                             False,
                                             "ECO:0000307"]}


def test_get_gaf_eco_map(map_cache):
    """
    Ensures the get_gaf_eco_map function is reading in the gaf-eco mappings correctly
    Two types of column layouts are found. If there is a "Default" present then we do not want it in the mapping key
    If there is a GO_REF (or any other value that may show up) we can include that here
    IEA     GO_REF:0000108  ECO:0000363
    IEP     Default ECO:0000270
    """
    assert type(map_cache) == type({})
    assert len(map_cache) > 0 # Don't want empty mapping

    # I can't imagine this file would grow from ~42 mappings --> 10,000 mappings.
    # "Helps" ensure correct file type is read in
    assert len(map_cache) < 10_000
    
    # Need to ensure each key, value pair is what we think it is
    for k, v in map_cache.items():
        
        # Basic types
        assert type(k) == type("hello")
        assert type(v) == type("hello")

        # Our "key" / "value" modeling checks
        assert v.startswith("ECO:")
        assert "Default" not in v # gaf-eco-mappings.txt formatting specific check
        assert "default" not in v # gaf-eco-mappings.txt formatting specific check

        assert "Default" not in k # gaf-eco-mappings.txt formatting specific check
        assert "default" not in k # gaf-eco-mappings.txt formatting specific check

        if "-" in k:
            assert k.split("-")[1].startswith("GO_REF:")


def test_association(basic_go):
    if not len(basic_go):
        logger.warning("test_association() null test?")
        return

    association = basic_go[2]
    assert association
    assert association.subject in result_expected.keys()

    assert association.object == result_expected[association.subject][2]
    assert association.predicate == result_expected[association.subject][5]
    assert association.negated == result_expected[association.subject][7]
    assert result_expected[association.subject][8] in association.has_evidence

    assert association.primary_knowledge_source == "infores:uniprot"
    assert "infores:monarchinitiative" in association.aggregator_knowledge_source

    # Taxon testing (multiple and single taxon values)
    single_taxa_association = basic_go[0]
    multi_taxa_association = basic_go[1]
    assert single_taxa_association.species_context_qualifier == result_expected[single_taxa_association.subject][1]
    assert multi_taxa_association.species_context_qualifier == result_expected[multi_taxa_association.subject][1]


def test_mgi_curie(mgi_entities):
    association = [association for association in mgi_entities if isinstance(association, Association)][0]
    assert association
    assert association.subject == "MGI:1918911"
    assert association.publications == ["MGI:2156816", "GO_REF:0000015"]
    assert association.primary_knowledge_source == "infores:mgi"
    assert "infores:monarchinitiative" in association.aggregator_knowledge_source