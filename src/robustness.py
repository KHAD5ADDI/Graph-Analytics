"""Test de robustesse du graphe d'ingredients.

Question : retirer les ingredients « ponts » (participation / intermediarite
elevees) deconnecte-t-il les cuisines davantage que retirer les ingredients
les plus frequents ou les plus connectes ? Si oui, le graphe voit une
structure que les simples frequences ne voient pas.

Strategies (classement fige sur le graphe d'origine, k ingredients retires) :
  - participation : coefficient de participation (ingredients de degre >= 20)
  - intermediarite : centralite d'intermediarite (distance = 1/poids)
  - frequence : nombre de recettes contenant l'ingredient
  - degre : nombre de voisins
  - aleatoire : moyenne de 20 tirages (baseline)

Metriques apres retrait :
  - lcc_frac : part des noeuds restants dans la plus grande composante
  - efficacite : efficacite globale (non ponderee)
  - arêtes inter-communautes : part du poids des aretes restantes qui relient
    deux communautes de la partition ORIGINALE (mesure les ponts perdus)
  - modularite : Louvain recalcule sur le graphe restant

Usage : python src/robustness.py
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
MIN_DEGREE_BRIDGE = 20
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


def evaluate(G0, removed, comm, with_louvain=True):
    G = G0.copy()
    G.remove_nodes_from(removed)
    eff, lcc = efficiency_and_lcc(G)
    row = {"efficacite": eff, "lcc_frac": lcc, "inter_communautes": cross_share(G, comm)}
    if with_louvain:
        part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
        row["modularite"] = nx.community.modularity(G, part, weight="weight")
    return row


def run(G, tag):
    part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
    comm = {n: i for i, c in enumerate(part) for n in c}
    pc = an.participation(G, part)
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d["dist"] = 1.0 / d["weight"]
    bet = nx.betweenness_centrality(H, weight="dist")

    cand = [n for n in G if G.degree(n) >= MIN_DEGREE_BRIDGE]
    ranks = {
        "participation": sorted(cand, key=lambda n: pc[n], reverse=True),
        "intermediarite": sorted(G, key=lambda n: bet[n], reverse=True),
        "frequence": sorted(G, key=lambda n: G.nodes[n]["n_recipes"], reverse=True),
        "degre": sorted(G, key=lambda n: G.degree(n), reverse=True),
    }

    # recouvrement des 20 premiers : les ponts sont-ils juste les plus frequents ?
    top = {k: set(v[:20]) for k, v in ranks.items()}
    print(f"\n[{tag}] recouvrement top-20 (Jaccard) avec 'frequence' :")
    for k in ("participation", "intermediarite", "degre"):
        j = len(top[k] & top["frequence"]) / len(top[k] | top["frequence"])
        print(f"  {k}: {j:.2f}")
    print(f"  top-10 participation : {ranks['participation'][:10]}")
    print(f"  top-10 intermediarite : {ranks['intermediarite'][:10]}")
    print(f"  top-10 frequence : {ranks['frequence'][:10]}")

    rows = []
    for strat, order in ranks.items():
        for k in KS:
            rows.append({"strategie": strat, "k": k, **evaluate(G, order[:k], comm)})

    rng = np.random.default_rng(SEED)
    nodes = list(G)
    rand = []
    for r in range(N_RANDOM):
        perm = list(rng.permutation(nodes))
        for k in KS:
            rand.append({"run": r, "k": k, **evaluate(G, perm[:k], comm, with_louvain=(r < 8))})
    rd = pd.DataFrame(rand).groupby("k").agg(["mean", "std"])
    for k in KS:
        rows.append({"strategie": "aleatoire", "k": k,
                     "efficacite": rd.loc[k, ("efficacite", "mean")],
                     "lcc_frac": rd.loc[k, ("lcc_frac", "mean")],
                     "inter_communautes": rd.loc[k, ("inter_communautes", "mean")],
                     "modularite": rd.loc[k, ("modularite", "mean")],
                     "efficacite_std": rd.loc[k, ("efficacite", "std")],
                     "inter_std": rd.loc[k, ("inter_communautes", "std")]})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"robustesse_{tag}.csv", index=False)

    # figure
    metrics = [("efficacite", "Efficacité globale"), ("lcc_frac", "Part de la plus grande composante"),
               ("inter_communautes", "Poids des arêtes inter-communautés"), ("modularite", "Modularité (Louvain)")]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4))
    colors = {"participation": "#d62728", "intermediarite": "#ff7f0e", "frequence": "#1f77b4",
              "degre": "#2ca02c", "aleatoire": "#7f7f7f"}
    for ax, (m, title) in zip(axes, metrics):
        for s, c in colors.items():
            d = df[df.strategie == s]
            ax.plot(d.k, d[m], marker="o", ms=3, label=s, color=c, ls="--" if s == "aleatoire" else "-")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Ingrédients retirés (k)")
    axes[0].legend(fontsize=8)
    fig.suptitle(f"Robustesse du graphe d'ingrédients — {tag} ({G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes)")
    fig.tight_layout()
    fig.savefig(OUT / f"robustesse_{tag}.png", dpi=130)
    plt.close(fig)

    piv = df.pivot(index="k", columns="strategie")
    for m in ("efficacite", "inter_communautes", "lcc_frac", "modularite"):
        print(f"\n[{tag}] {m} :\n", piv[m].round(3))
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
