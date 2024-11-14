from pathlib import Path

import duckdb

nodes_file = "output/go_annotation_nodes.tsv"
nodes_report = "output/go_annotation_nodes_report.tsv"

edges_file = "output/go_annotation_edges.tsv"
edges_report = "output/go_annotation_edges_report.tsv"


# Nodes
if Path(nodes_file).exists():
    query = f"""
    SELECT category, split_part(id, ':', 1) as prefix, count(*)
    FROM '{nodes_file}'
    GROUP BY all
    ORDER BY all
    """

    ncommand = "copy ({}) to '{}' (header, delimiter '\t')".format(query, nodes_report)
    duckdb.sql(ncommand)

# Edges
if Path(edges_file).exists():
    query = f"""
    SELECT category, split_part(subject, ':', 1) as subject_prefix, predicate,
    split_part(object, ':', 1) as object_prefix, count(*)
    FROM '{edges_file}'
    GROUP BY all
    ORDER BY all
    """
    ecommand = "copy ({}) to '{}' (header, delimiter '\t')".format(query, edges_report)
    duckdb.sql(ecommand)
