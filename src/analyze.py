"""Required measures, Louvain communities, centralities and threshold sensitivity.

Conventions (to state in the report):
- diameter and radius: largest connected component, UNWEIGHTED graph (number of hops)
- hop betweenness (primary): every edge counts as one step; NetworkX normalises it
  by default, so values are shares of shortest paths
- weighted betweenness (sensitivity): distance = 1 / weight (a stronger association
  or similarity means a shorter step); the weight is PMI for ingredients and
  Jaccard for countries
- eigenvector centrality: defined on the largest connected component only (code kept,
  not used in the report)
- Louvain: weighted graph, communities numbered by decreasing size (ties broken by the
  alphabetically smallest member), so every script and table uses the same numbering
- participation coefficient P_i = 1 - sum_c (k_ic / k_i)^2 (Guimera & Amaral): kept in
  the repository only, it is not part of the report

Usage: python src/analyze.py
"""
from pathlib import Path

import networkx as nx
import pandas as pd

import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42


def louvain_partition(G, seed=SEED):
    """Louvain communities, sorted by decreasing size (community 0 is the largest).

    Ties are broken by the smallest member name so the numbering is reproducible.
    """
    part = nx.community.louvain_communities(G, weight="weight", seed=seed)
    return sorted(part, key=lambda c: (-len(c), min(c)))


def community_map(part):
    return {n: i for i, c in enumerate(part) for n in c}


def participation(G, part):
    comm = community_map(part)
    res = {}
    for n in G:
        k = G.degree(n)
        if k == 0:
            res[n] = 0.0
            continue
        cnt = {}
        for nb in G[n]:
            cnt[comm[nb]] = cnt.get(comm[nb], 0) + 1
        res[n] = 1 - sum((v / k) ** 2 for v in cnt.values())
    return res


def global_measures(G, seed=SEED):
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    lcc = G.subgraph(comps[0])
    part = louvain_partition(G, seed)
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "components": len(comps),
        "lcc_size": lcc.number_of_nodes(),
        "diameter_lcc": nx.diameter(lcc) if lcc.number_of_nodes() > 1 else 0,
        "radius_lcc": nx.radius(lcc) if lcc.number_of_nodes() > 1 else 0,
        "avg_clustering": round(nx.average_clustering(G), 3),
        "louvain_communities": len(part),
        "modularity": round(nx.community.modularity(G, part, weight="weight"), 3),
    }, part


def node_table(G, part, weight_name):
    """One row per node. weight_name labels the weighted-betweenness column
    ('pmi' for ingredients, 'jaccard' for countries)."""
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d["dist"] = 1.0 / d["weight"]
    # eigenvector centrality: largest connected component only
    lcc = G.subgraph(max(nx.connected_components(G), key=len))
    eig = nx.eigenvector_centrality_numpy(lcc, weight="weight")
    df = pd.DataFrame({
        "degree": dict(G.degree()),
        "strength": dict(G.degree(weight="weight")),
        "betweenness_hop": nx.betweenness_centrality(G),
        f"betweenness_{weight_name}": nx.betweenness_centrality(H, weight="dist"),
        "eigenvector": eig,
        "community": community_map(part),
        "participation": participation(G, part),
    })
    df.index.name = "node"
    return df.sort_values(["betweenness_hop", "degree"], ascending=False)


def sensitivity_ingredients(pairs, names):
    rows = []
    for min_cooc in (5, 10, 20, 50):
        for pmi in (0.0, 0.5, 1.0):
            G = bg.build_ingredient_graph(pairs, names, min_cooc=min_cooc, pmi_thr=pmi)
            m, _ = global_measures(G)
            rows.append({"min_cooccurrence": min_cooc, "pmi_threshold": pmi, **m})
    return pd.DataFrame(rows)


def sensitivity_countries(mode):
    prof = bg.load_country_profiles(mode)
    rows = []
    for thr in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
        G, _ = bg.build_country_graph(prof, jaccard_thr=thr)
        m, _ = global_measures(G)
        rows.append({"profile": mode, "jaccard_threshold": thr, **m})
    return pd.DataFrame(rows)


def describe_communities(G, part, n_top=8):
    for k, c in enumerate(part[:6]):
        top = sorted(c, key=lambda n: G.degree(n, weight="weight"), reverse=True)[:n_top]
        print(f"community {k} ({len(c)} nodes), strongest members: {', '.join(top)}")


def main():
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)

    # --- Ingredient graph ---
    recipes, pairs, names = bg.load_culinarydb()
    Gi = bg.build_ingredient_graph(pairs, names)
    mi, part_i = global_measures(Gi)
    ti = node_table(Gi, part_i, "pmi")
    ti.to_csv(OUT / "ingredients_nodes.csv", encoding="utf-8-sig")
    print("== INGREDIENTS ==")
    print(mi)
    print("\nTop 10 by hop betweenness (primary):\n", ti.head(10).round(3))
    print("\nTop 10 by 1/PMI betweenness (sensitivity):\n",
          ti.sort_values("betweenness_pmi", ascending=False).head(10).round(3))
    print("\nTop 10 by participation coefficient, degree >= 20 (repository only):\n",
          ti[ti.degree >= 20].sort_values("participation", ascending=False).head(10).round(3))
    describe_communities(Gi, part_i)

    s_i = sensitivity_ingredients(pairs, names)
    s_i.to_csv(OUT / "sensibilite_ingredients.csv", index=False)
    print("\nSensitivity, ingredients:\n", s_i)

    # --- Country graph ---
    print("\n== COUNTRIES ==")
    for mode in ("all", "national"):
        prof = bg.load_country_profiles(mode)
        Gc, _ = bg.build_country_graph(prof)
        mc, part_c = global_measures(Gc)
        print(f"\nprofile={mode} (Jaccard threshold {bg.JACCARD_THRESHOLD}):", mc)
        if mode == bg.COUNTRY_PROFILE:
            tc = node_table(Gc, part_c, "jaccard")
            tc.to_csv(OUT / "countries_nodes.csv", encoding="utf-8-sig")
            print("Top 10 by hop betweenness:\n", tc.head(10).round(3))
            for k, c in enumerate(part_c):
                print(f"community {k} ({len(c)}):", ", ".join(sorted(c)[:14]))
    s_c = pd.concat([sensitivity_countries("all"), sensitivity_countries("national")])
    s_c.to_csv(OUT / "sensibilite_pays.csv", index=False)
    print("\nSensitivity, countries:\n", s_c)


if __name__ == "__main__":
    main()
