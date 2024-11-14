from pathlib import Path

from kgx.cli.cli_utils import transform as kgx_transform
from loguru import logger


src_files = []
outfile = "output/go_annotation_associations.nt.gz"
src_nodes = "output/go_annotation_nodes.tsv"
src_edges = "output/go_annotation_edges.tsv"

logger.info("Creating rdf output: {}...".format(outfile))

if Path(src_nodes).is_file():
    src_files.append(src_nodes)
if Path(src_edges).is_file():
    src_files.append(src_edges)

kgx_transform(inputs=src_files,
              input_format="tsv",
              stream=True,
              output=outfile,
              output_format="nt",
              output_compression="gz")
