"""Numbers behind the choice of PMI as the ingredient edge weight.

Shared-recipe counts answer "which ingredients appear together most often?".
PMI answers "which pairs appear together more often than their frequencies predict?".

PMI(i, j) = log2( c_ij * N / (c_i * c_j) ), where c_ij is the number of recipes containing
both ingredients, c_i and c_j the numbers of recipes containing each one, and N the
number of recipes with at least one ingredient. A positive value means the pair occurs
more often than if the two ingredients were independent; it is not a significance test.

Saved to outputs/:
  - pmi_examples.csv: observed vs expected recipes for two pairs (Salt-Garlic, Ginger-Soybean Sauce)
  - pmi_vs_counts.csv: on the SAME edges, Louvain with PMI weights vs shared-recipe counts
    as weights (communities, modularity), and the Spearman correlation of each strength
    with ingredient frequency. The two modularities are not comparable across graphs with
    different edges, which is why the comparison keeps the edge set fixed.

Usage: python src/pmi_justification.py
"""
from pathlib import Path

import networkx as nx
import pandas as pd
from scipy.stats import spearmanr

import analyze as an
import build_graphs as bg

OUT = Path(__file__).resolve().parent.parent / "outputs"


def main():
    OUT.mkdir(exist_ok=True)
    recipes, pairs, names = bg.load_culinarydb()
    G = bg.build_ingredient_graph(pairs, names)
    n_rec = pairs["recipe"].nunique()
    node_entity = {n: d["entity"] for n, d in G.nodes(data=True)}
    recipes_of = {n: set(pairs.loc[pairs.entity == e, "recipe"]) for n, e in node_entity.items()
                  if n in ("Salt", "Garlic", "Ginger", "Soybean Sauce")}

    rows = []
    for a, b in (("Salt", "Garlic"), ("Ginger", "Soybean Sauce")):
        together = len(recipes_of[a] & recipes_of[b])
        expected = len(recipes_of[a]) * len(recipes_of[b]) / n_rec
        rows.append({"pair": f"{a} - {b}", "recipes_with_a": len(recipes_of[a]),
                     "recipes_with_b": len(recipes_of[b]), "recipes_together": together,
                     "expected_if_independent": round(expected, 1),
                     "ratio": round(together / expected, 2), "pmi": round(G[a][b]["weight"], 3),
                     "n_recipes": n_rec})
    ex = pd.DataFrame(rows)
    ex.to_csv(OUT / "pmi_examples.csv", index=False)
    print(ex.to_string(index=False))

    # same edges, weights = number of shared recipes
    H = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, d in G.edges(data=True):
        H.add_edge(u, v, weight=d["cooc"])
    freq = pd.Series({n: d["n_recipes"] for n, d in G.nodes(data=True)})
    out = []
    for label, graph in (("PMI weights", G), ("shared-recipe counts", H)):
        part = an.louvain_partition(graph)
        strength = pd.Series(dict(graph.degree(weight="weight")))
        rho, _ = spearmanr(strength.loc[freq.index], freq)
        out.append({"weights": label, "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
                    "louvain_communities": len(part),
                    "modularity": round(nx.community.modularity(graph, part, weight="weight"), 3),
                    "spearman_strength_vs_frequency": round(rho, 3)})
    cmp_ = pd.DataFrame(out)
    cmp_.to_csv(OUT / "pmi_vs_counts.csv", index=False)
    print("\nSame edges, different weights:\n", cmp_.to_string(index=False))


if __name__ == "__main__":
    main()
