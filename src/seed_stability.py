"""Stability of the Louvain communities over 30 random seeds.

Louvain is a randomised heuristic: different seeds can give different partitions.
For both graphs we run it with seeds 0..29 and save:
  - outputs/louvain_seeds.csv: one row per seed (number of communities, modularity,
    community sizes); seed 42, used everywhere else in the project, is added as a
    reference row
  - outputs/louvain_seed_summary.csv: number of communities (min, max, most frequent)
    and modularity range for each graph
  - outputs/louvain_recurring_groups.csv: groups of nodes that stay together. Two nodes
    are linked if they share a community in at least 90 % of the seeds (27 of 30); a
    group is a connected set of such nodes (singletons are not listed).

No NMI or ARI is used: stability is described with community counts, the modularity
range and the groups that recur.

Usage: python src/seed_stability.py
"""
from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

import analyze as an
import build_graphs as bg

OUT = Path(__file__).resolve().parent.parent / "outputs"
SEEDS = list(range(30))
REFERENCE_SEED = an.SEED
SHARE = 0.9


def run_graph(label, G):
    rows, labels = [], []
    nodes = list(G)
    for seed in SEEDS + [REFERENCE_SEED]:
        part = an.louvain_partition(G, seed)
        comm = an.community_map(part)
        rows.append({"graph": label, "seed": seed, "reference_seed": seed == REFERENCE_SEED,
                     "n_communities": len(part),
                     "modularity": nx.community.modularity(G, part, weight="weight"),
                     "community_sizes": " ".join(str(len(c)) for c in part)})
        if seed in SEEDS:
            labels.append(np.array([comm[n] for n in nodes]))
    runs = pd.DataFrame(rows)

    # co-membership frequency over the 30 seeds
    co = sum((l[:, None] == l[None, :]).astype(int) for l in labels)
    need = int(np.ceil(SHARE * len(SEEDS)))
    A = nx.Graph()
    A.add_nodes_from(range(len(nodes)))
    ii, jj = np.where(np.triu(co >= need, k=1))
    A.add_edges_from(zip(ii.tolist(), jj.tolist()))
    strength = dict(G.degree(weight="weight"))
    groups = []
    for comp in sorted(nx.connected_components(A), key=lambda c: (-len(c), min(c))):
        if len(comp) < 2:
            continue
        members = sorted((nodes[i] for i in comp), key=lambda n: -strength[n])
        groups.append({"graph": label, "group": len(groups), "size": len(members),
                       "min_share_of_seeds": SHARE, "strongest_members": "; ".join(members[:10])})
    singles = sum(1 for c in nx.connected_components(A) if len(c) == 1)

    only = runs[~runs.reference_seed]
    counts = Counter(only.n_communities)
    summary = {"graph": label, "n_seeds": len(SEEDS),
               "communities_min": int(only.n_communities.min()), "communities_max": int(only.n_communities.max()),
               "communities_most_frequent": counts.most_common(1)[0][0],
               "runs_with_most_frequent": counts.most_common(1)[0][1],
               "modularity_min": only.modularity.min(), "modularity_max": only.modularity.max(),
               "modularity_mean": only.modularity.mean(),
               "recurring_groups": len(groups), "nodes_in_recurring_groups": sum(g["size"] for g in groups),
               "nodes_without_recurring_group": singles,
               "reference_seed_communities": int(runs[runs.reference_seed].n_communities.iloc[0]),
               "reference_seed_modularity": runs[runs.reference_seed].modularity.iloc[0]}
    return runs, summary, groups, dict(sorted(counts.items()))


def main():
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 120)
    recipes, pairs, names = bg.load_culinarydb()
    Gi = bg.build_ingredient_graph(pairs, names)
    Gc, _ = bg.build_country_graph(bg.load_country_profiles())

    all_runs, summaries, all_groups = [], [], []
    for label, G in (("ingredients", Gi), ("countries", Gc)):
        runs, summary, groups, dist = run_graph(label, G)
        all_runs.append(runs); summaries.append(summary); all_groups += groups
        print(f"\n== {label} ==")
        print(f"communities over {len(SEEDS)} seeds: {summary['communities_min']} to {summary['communities_max']} "
              f"(distribution {dist}); modularity {summary['modularity_min']:.3f} to {summary['modularity_max']:.3f}")
        print(f"seed {REFERENCE_SEED} (reference): {summary['reference_seed_communities']} communities, "
              f"modularity {summary['reference_seed_modularity']:.3f}")
        print(f"recurring groups (>= {int(np.ceil(SHARE * len(SEEDS)))} of {len(SEEDS)} seeds): {summary['recurring_groups']} groups "
              f"covering {summary['nodes_in_recurring_groups']} nodes; {summary['nodes_without_recurring_group']} nodes without a stable partner")
        for g in groups[:8]:
            print(f"  group {g['group']} ({g['size']}): {g['strongest_members']}")

    pd.concat(all_runs).to_csv(OUT / "louvain_seeds.csv", index=False)
    pd.DataFrame(summaries).to_csv(OUT / "louvain_seed_summary.csv", index=False)
    pd.DataFrame(all_groups).to_csv(OUT / "louvain_recurring_groups.csv", index=False)


if __name__ == "__main__":
    main()
