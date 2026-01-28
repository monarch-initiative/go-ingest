"""Tests for the GAF-ECO map preprocessing script."""

import tempfile
from pathlib import Path

import duckdb
import pytest


@pytest.fixture
def sql_template():
    """Load the SQL template with placeholders for input/output paths."""
    sql_file = Path(__file__).parent.parent / "scripts" / "preprocess_gaf_eco_map.sql"
    return sql_file.read_text()


def run_preprocessing(input_content: str, sql_template: str) -> list[dict]:
    """Run preprocessing SQL on input content and return results as list of dicts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create input file
        data_dir = tmpdir / "data"
        data_dir.mkdir()
        input_file = data_dir / "gaf-eco-mapping.txt"
        input_file.write_text(input_content)

        # Modify SQL to use temp paths
        sql = sql_template.replace(
            "'data/gaf-eco-mapping.txt'",
            f"'{input_file}'"
        ).replace(
            "'data/gaf-eco-map.tsv'",
            f"'{data_dir / 'gaf-eco-map.tsv'}'"
        )

        # Run the SQL
        con = duckdb.connect(":memory:")
        con.execute(sql)

        # Read results from the table (before it's exported)
        results = con.execute("SELECT * FROM gaf_eco_map ORDER BY evidence_code").fetchall()
        columns = ["evidence_code", "eco_term"]

        con.close()

        return [dict(zip(columns, row)) for row in results]


class TestGafEcoMapPreprocessing:
    """Tests for GAF-ECO mapping preprocessing."""

    def test_skips_comment_lines(self, sql_template):
        """Comment lines starting with # should be skipped."""
        input_content = """# This is a comment
# Another comment
EXP	Default	ECO:0000269
# Comment in the middle
IDA	Default	ECO:0000314
"""
        results = run_preprocessing(input_content, sql_template)

        assert len(results) == 2
        assert results[0]["evidence_code"] == "EXP"
        assert results[1]["evidence_code"] == "IDA"

    def test_default_qualifier_uses_simple_key(self, sql_template):
        """When qualifier is 'Default', use code as-is for key."""
        input_content = """EXP	Default	ECO:0000269
IDA	Default	ECO:0000314
"""
        results = run_preprocessing(input_content, sql_template)

        assert len(results) == 2
        assert results[0]["evidence_code"] == "EXP"
        assert results[0]["eco_term"] == "ECO:0000269"
        assert results[1]["evidence_code"] == "IDA"
        assert results[1]["eco_term"] == "ECO:0000314"

    def test_non_default_qualifier_creates_compound_key(self, sql_template):
        """When qualifier is not 'Default', create compound key: code-qualifier."""
        input_content = """IDA	UniProtKB	ECO:0000314
IEA	InterPro	ECO:0000501
EXP	Default	ECO:0000269
"""
        results = run_preprocessing(input_content, sql_template)

        assert len(results) == 3
        # Results are sorted alphabetically by evidence_code
        assert results[0]["evidence_code"] == "EXP"
        assert results[0]["eco_term"] == "ECO:0000269"
        assert results[1]["evidence_code"] == "IDA-UniProtKB"
        assert results[1]["eco_term"] == "ECO:0000314"
        assert results[2]["evidence_code"] == "IEA-InterPro"
        assert results[2]["eco_term"] == "ECO:0000501"

    def test_case_insensitive_default_check(self, sql_template):
        """The 'Default' check should be case-insensitive."""
        input_content = """EXP	default	ECO:0000269
IDA	DEFAULT	ECO:0000314
IMP	DeFaUlT	ECO:0000315
"""
        results = run_preprocessing(input_content, sql_template)

        # All should use simple keys since they're variations of "default"
        assert len(results) == 3
        assert results[0]["evidence_code"] == "EXP"
        assert results[1]["evidence_code"] == "IDA"
        assert results[2]["evidence_code"] == "IMP"

    def test_whitespace_in_qualifier_trimmed(self, sql_template):
        """Whitespace around qualifier should be trimmed."""
        input_content = """EXP	 Default 	ECO:0000269
IDA	  default  	ECO:0000314
"""
        results = run_preprocessing(input_content, sql_template)

        assert len(results) == 2
        assert results[0]["evidence_code"] == "EXP"
        assert results[1]["evidence_code"] == "IDA"

    def test_output_sorted_by_evidence_code(self, sql_template):
        """Output should be sorted alphabetically by evidence_code."""
        input_content = """TAS	Default	ECO:0000304
EXP	Default	ECO:0000269
IDA	Default	ECO:0000314
"""
        results = run_preprocessing(input_content, sql_template)

        codes = [r["evidence_code"] for r in results]
        assert codes == sorted(codes)

    def test_real_mapping_file_row_count(self, sql_template):
        """Test with actual content from gaf-eco-mapping.txt."""
        # This is the actual content from the mapping file (26 mappings)
        input_content = """# Comment header
EXP	Default	ECO:0000269
HDA	Default	ECO:0007005
HEP	Default	ECO:0007007
HGI	Default	ECO:0007003
HMP	Default	ECO:0007001
HTP	Default	ECO:0006056
IBA	Default	ECO:0000318
IBD	Default	ECO:0000319
IC	Default	ECO:0000305
IDA	Default	ECO:0000314
IEA	Default	ECO:0000501
IEP	Default	ECO:0000270
IGC	Default	ECO:0000317
IGI	Default	ECO:0000316
IKR	Default	ECO:0000320
IMP	Default	ECO:0000315
IPI	Default	ECO:0000353
IRD	Default	ECO:0000321
ISA	Default	ECO:0000247
ISM	Default	ECO:0000255
ISO	Default	ECO:0000266
ISS	Default	ECO:0000250
NAS	Default	ECO:0000303
ND	Default	ECO:0000307
RCA	Default	ECO:0000245
TAS	Default	ECO:0000304
"""
        results = run_preprocessing(input_content, sql_template)

        assert len(results) == 26

        # Spot check a few mappings
        results_dict = {r["evidence_code"]: r["eco_term"] for r in results}
        assert results_dict["EXP"] == "ECO:0000269"
        assert results_dict["IEA"] == "ECO:0000501"
        assert results_dict["ND"] == "ECO:0000307"
