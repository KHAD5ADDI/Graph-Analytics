"""Removal experiments on the ingredient graph (repository only, not in the report).

Question: does removing the ingredients with the highest participation coefficient or
betweenness disconnect the cuisines more than removing frequent ingredients?

Strategies (ranking fixed on the original graph, k ingredients removed):
  - participation: participation coefficient (ingredients of degree >= 20)
  - betweenness_hop: hop betweenness (primary broker measure)
  - betweenness_pmi: betweenness with distance 1/PMI (sensitivity)
  - frequency: number of recipes containing the ingredient
  - degree: number of neighbours
  - random: mean of 20 draws (baseline)

Metrics after removal:
  - lcc_frac: share of the remaining nodes in the largest component
  - efficiency: global efficiency (unweighted)
  - inter_community_weight: share of the remaining edge weight joining two communities of
    the ORIGINAL partition (partly circular for the participation strategy, which is
    defined with the same partition)
  - modularity: Louvain recomputed on the remaining graph

The modularity of the random baseline is computed on all 20 draws.

Usage: python src/robustness.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components, shortest_path

import analyze as an
import build_graphs as bg

OUT = Path(__file__).resolve().parent.parent / "outputs"
KS = [0, 5, 10, 15, 20, 30, 40, 60]
N_RANDOM = 20
MIN_DEGREE_PARTICIPATION = 20
SEED = 42


def efficiency_and_lcc(G):
    nodes = list(G)
    n = len(nodes)
    if n < 2:
        return 0.0, 0.0
    A = nx.to_scipy_sparse_array(G, nodelist=nodes, weight=None, format="csr")
    ncomp, labels = connected_components(A, directed=False)
    lcc = np.bincount(labels).max() / n
    D = shortest_path(A, unweighted=True, directed=False)
    with np.errstate(divide="ignore"):
        inv = np.where(np.isinf(D) | (D == 0), 0.0, 1.0 / D)
    return inv.sum() / (n * (n - 1)), lcc


def cross_share(G, comm):
    tot = cross = 0.0
    for u, v, d in G.edges(data=True):
        tot += d["weight"]
        if comm[u] != comm[v]:
            cross += d["weight"]
    return cross / tot if tot else 0.0


def evaluate(G0, removed, comm):
    G = G0.copy()
    G.remove_nodes_from(removed)
    eff, lcc = efficiency_and_lcc(G)
    part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
    return {"efficiency": eff, "lcc_frac": lcc,
            "inter_community_weight": cross_share(G, comm),
            "modularity": nx.community.modularity(G, part, weight="weight")}


def run(G, tag):
    part = an.louvain_partition(G)
    comm = an.community_map(part)
    pc = an.participation(G, part)
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d["dist"] = 1.0 / d["weight"]
    bet_hop = nx.betweenness_centrality(G)
    bet_pmi = nx.betweenness_centrality(H, weight="dist")

    cand = [n for n in G if G.degree(n) >= MIN_DEGREE_PARTICIPATION]
    ranks = {
        "participation": sorted(cand, key=lambda n: pc[n], reverse=True),
        "betweenness_hop": sorted(G, key=lambda n: bet_hop[n], reverse=True),
        "betweenness_pmi": sorted(G, key=lambda n: bet_pmi[n], reverse=True),
        "frequency": sorted(G, key=lambda n: G.nodes[n]["n_recipes"], reverse=True),
        "degree": sorted(G, key=lambda n: G.degree(n), reverse=True),
    }

    # overlap of the top 20 with the top 20 by frequency
    top = {k: set(v[:20]) for k, v in ranks.items()}
    print(f"\n[{tag}] top-20 overlap (Jaccard) with 'frequency':")
    for k in ("participation", "betweenness_hop", "betweenness_pmi", "degree"):
        j = len(top[k] & top["frequency"]) / len(top[k] | top["frequency"])
        print(f"  {k}: {j:.2f}")
    for k in ("participation", "betweenness_hop", "betweenness_pmi", "frequency"):
        print(f"  top-10 {k}: {ranks[k][:10]}")

    rows = []
    for strat, order in ranks.items():
        for k in KS:
            rows.append({"strategy": strat, "k": k, **evaluate(G, order[:k], comm)})

    rng = np.random.default_rng(SEED)
    nodes = list(G)
    rand = []
    for r in range(N_RANDOM):
        perm = list(rng.permutation(nodes))
        for k in KS:
            rand.append({"run": r, "k": k, **evaluate(G, perm[:k], comm)})
    rd = pd.DataFrame(rand).groupby("k").agg(["mean", "std"])
    for k in KS:
        rows.append({"strategy": "random", "k": k,
                     "efficiency": rd.loc[k, ("efficiency", "mean")],
                     "lcc_frac": rd.loc[k, ("lcc_frac", "mean")],
                     "inter_community_weight": rd.loc[k, ("inter_community_weight", "mean")],
                     "modularity": rd.loc[k, ("modularity", "mean")],
                     "efficiency_std": rd.loc[k, ("efficiency", "std")],
                     "inter_community_std": rd.loc[k, ("inter_community_weight", "std")],
                     "modularity_std": rd.loc[k, ("modularity", "std")],
                     "n_random_draws": N_RANDOM})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"robustesse_{tag}.csv", index=False)

    metrics = [("efficiency", "Global efficiency"), ("lcc_frac", "Share in the largest component"),
               ("inter_community_weight", "Inter-community edge weight"), ("modularity", "Modularity (Louvain)")]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4))
    colors = {"participation": "#d62728", "betweenness_hop": "#ff7f0e", "betweenness_pmi": "#9467bd",
              "frequency": "#1f77b4", "degree": "#2ca02c", "random": "#7f7f7f"}
    for ax, (m, title) in zip(axes, metrics):
        for s, c in colors.items():
            d = df[df.strategy == s]
            ax.plot(d.k, d[m], marker="o", ms=3, label=s, color=c, ls="--" if s == "random" else "-")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Ingredients removed (k)")
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Removal experiments, ingredient graph: {tag} ({G.number_of_nodes()} nodes, "
                 f"{G.number_of_edges()} edges; random = mean of {N_RANDOM} draws)")
    fig.tight_layout()
    fig.savefig(OUT / f"robustesse_{tag}.png", dpi=130)
    plt.close(fig)

    piv = df.pivot(index="k", columns="strategy")
    for m in ("efficiency", "inter_community_weight", "lcc_frac", "modularity"):
        print(f"\n[{tag}] {m}:\n", piv[m].round(3))
    return df


def main():
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 200)
    recipes, pairs, names = bg.load_culinarydb()
    G = bg.build_ingredient_graph(pairs, names)
    run(G, "defaut")
    G2 = bg.build_ingredient_graph(pairs, names, min_cooc=20, pmi_thr=0.5)
    run(G2, "epure_pmi0.5_cooc20")


if __name__ == "__main__":
    main()
