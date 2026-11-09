"""Network figures of the two graphs (report figures).

Outputs (outputs/):
  - fig_ingredients.png: ingredient graph, colour = Louvain community, size = strength
    (sum of PMI), black ring + label = the 10 ingredients with the highest hop
    betweenness ("brokers", the primary measure). Labels: the 4 strongest ingredients
    of each of the 6 largest communities.
  - fig_pays.png: country graph, Louvain communities on the left, UN regions on the
    right (same layout, to compare them)

For readability only the strongest edges of each node are drawn and used for the
layout (a backbone). All measures in the report are computed on the full graphs.
Node positions come from a force-directed layout and have no geographic meaning.
Communities are numbered by decreasing size (see analyze.louvain_partition).

Usage: python src/visualize.py   (needs outputs/geo_pays_communautes.csv from geography.py)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

import analyze as an
import build_graphs as bg

OUT = Path(__file__).resolve().parent.parent / "outputs"
SEED = 42
N_BROKERS = 10
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
           "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295"]


def backbone(G, k):
    """Union of the k strongest edges of each node (display only)."""
    keep = set()
    for n in G:
        nb = sorted(G[n].items(), key=lambda x: x[1]["weight"], reverse=True)[:k]
        keep.update(tuple(sorted((n, m))) for m, _ in nb)
    B = nx.Graph()
    B.add_nodes_from(G.nodes(data=True))
    B.add_edges_from((u, v, G[u][v]) for u, v in keep)
    return B


def draw(ax, G, B, pos, colors, sizes, edge_alpha=0.12, edge_width=0.4):
    w = np.array([B[u][v]["weight"] for u, v in B.edges()])
    lw = edge_width + 1.2 * (w - w.min()) / (np.ptp(w) + 1e-9)
    nx.draw_networkx_edges(B, pos, ax=ax, width=lw, alpha=edge_alpha, edge_color="#555555")
    nx.draw_networkx_nodes(B, pos, ax=ax, node_color=colors, node_size=sizes,
                           linewidths=0.4, edgecolors="white")
    ax.set_axis_off()


SHORT = {"Saint Vincent and the Grenadines": "St Vincent", "Lao People's Democratic Republic": "Laos",
         "Korea, Rep. of Korea": "Korea", "Bosnia and Herzegovina": "Bosnia", "Saint Kitts and Nevis": "St Kitts",
         "Micronesia (Federated States of)": "Micronesia", "Iran (Islamic Republic of)": "Iran",
         "Tanzania, United Rep. of": "Tanzania", "Antigua and Barbuda": "Antigua",
         "Republic of the Congo": "Congo", "United States of America": "USA"}


def label(ax, pos, nodes, fs=9, weight="normal"):
    for n in nodes:
        x, y = pos[n]
        ax.text(x, y, SHORT.get(n, n), fontsize=fs, ha="center", va="center", fontweight=weight,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75), zorder=5)


def fig_ingredients():
    recipes, pairs, names = bg.load_culinarydb()
    G = bg.build_ingredient_graph(pairs, names)
    part = an.louvain_partition(G)
    comm = an.community_map(part)
    strength = dict(G.degree(weight="weight"))
    hop = nx.betweenness_centrality(G)
    brokers = sorted(G, key=lambda n: hop[n], reverse=True)[:N_BROKERS]

    B = backbone(G, 6)
    pos = nx.spring_layout(B, weight="weight", k=0.35, iterations=300, seed=SEED)
    sizes = [30 + 3.0 * strength[n] for n in B]
    colors = [PALETTE[comm[n] % len(PALETTE)] for n in B]

    fig, ax = plt.subplots(figsize=(15, 12))
    draw(ax, G, B, pos, colors, sizes)
    nx.draw_networkx_nodes(B, pos, nodelist=brokers, ax=ax, node_color="none",
                           node_size=[30 + 3.0 * strength[n] + 60 for n in brokers],
                           edgecolors="black", linewidths=1.8)
    hubs = []
    for c in part[:6]:
        hubs += sorted(c, key=lambda n: strength[n], reverse=True)[:4]
    label(ax, pos, [n for n in dict.fromkeys(hubs) if n not in brokers], fs=9)
    label(ax, pos, brokers, fs=10, weight="bold")

    handles = []
    for i, c in enumerate(part[:6]):
        top = ", ".join(sorted(c, key=lambda n: strength[n], reverse=True)[:3])
        handles.append(plt.Line2D([], [], marker="o", ls="", color=PALETTE[i], ms=10,
                                  label=f"Community {i} ({len(c)} ingredients): {top}"))
    handles.append(plt.Line2D([], [], marker="o", ls="", mfc="none", mec="black", mew=1.8, ms=11,
                              label=f"Broker: top {N_BROKERS} by hop betweenness"))
    ax.legend(handles=handles, loc="lower left", fontsize=10, frameon=True)
    ax.set_title(f"Ingredient graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
                 f"(drawn: {B.number_of_edges()} edges, the strongest ones of each node)\n"
                 "Source: CulinaryDB (CoSyLab, IIIT-Delhi)", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ingredients.png", dpi=150)
    plt.close(fig)
    print("fig_ingredients.png, brokers:", brokers)


def fig_countries():
    prof = bg.load_country_profiles("all")
    G, _ = bg.build_country_graph(prof)
    geo = pd.read_csv(OUT / "geo_pays_communautes.csv", encoding="utf-8-sig").set_index("country")
    comm = geo["community"].to_dict()
    region = geo["region"].to_dict()
    strength = dict(G.degree(weight="weight"))

    B = backbone(G, 5)
    # layout on the largest connected component; the other countries go in a row at the bottom
    comps = sorted(nx.connected_components(B), key=len, reverse=True)
    main = B.subgraph(comps[0])
    pos = nx.spring_layout(main, weight="weight", k=0.22, iterations=500, seed=SEED)
    ys = [p[1] for p in pos.values()]
    xs = [p[0] for p in pos.values()]
    rest = [n for c in comps[1:] for n in sorted(c)]
    y0 = min(ys) - 0.18 * (max(ys) - min(ys))
    for i, n in enumerate(rest):
        pos[n] = (min(xs) + (max(xs) - min(xs)) * (i + 0.5) / max(len(rest), 1), y0)
    sizes = [25 + 5.0 * strength[n] for n in B]

    regs = ["Europe", "Asia", "Africa", "Americas", "Oceania"]
    reg_col = dict(zip(regs, ["#4e79a7", "#e15759", "#59a14f", "#f28e2b", "#b07aa1"]))

    fig, axes = plt.subplots(1, 2, figsize=(22, 10))
    draw(axes[0], G, B, pos, [PALETTE[comm[n] % len(PALETTE)] for n in B], sizes, edge_alpha=0.10)
    draw(axes[1], G, B, pos, [reg_col[region[n]] for n in B], sizes, edge_alpha=0.10)

    sizes_c = pd.Series(comm).value_counts()
    big = list(sizes_c.sort_index().index[:6])   # numbering is by size, so 0..5 are the largest
    hubs = []
    for c in big:
        members = [n for n in G if comm[n] == c and n in main]
        hubs += sorted(members, key=lambda n: strength[n], reverse=True)[:2]
    hubs = list(dict.fromkeys(hubs))
    span = max(ys) - min(ys)
    for ax in axes:
        label(ax, pos, hubs, fs=9)
        for n in rest:   # labels under the points so they do not hide them
            ax.text(pos[n][0], pos[n][1] - 0.035 * span, SHORT.get(n, n), fontsize=8.5, ha="center", va="top")
        ax.text(min(xs), y0 + 0.06 * span, "Countries outside the largest connected component:",
                fontsize=9, style="italic", ha="left")
        ax.set_ylim(y0 - 0.12 * span, max(ys) + 0.05 * span)

    h0 = [plt.Line2D([], [], marker="o", ls="", color=PALETTE[c % len(PALETTE)], ms=10,
                     label=f"Community {c} ({sizes_c[c]})") for c in big]
    axes[0].legend(handles=h0, loc="upper left", fontsize=10)
    h1 = [plt.Line2D([], [], marker="o", ls="", color=reg_col[r], ms=10, label=r) for r in regs]
    axes[1].legend(handles=h1, loc="upper left", fontsize=10)
    axes[0].set_title("Detected communities (Louvain)", fontsize=13)
    axes[1].set_title("UN regions (same layout)", fontsize=13)
    fig.suptitle(f"Country graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
                 f"(Jaccard >= {bg.JACCARD_THRESHOLD}), drawn: {B.number_of_edges()} edges, the strongest ones of each node\n"
                 "Source: Wunderlich & Kohler (2022), EnviDat", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "fig_pays.png", dpi=130)
    plt.close(fig)
    print("fig_pays.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_ingredients()
    fig_countries()
