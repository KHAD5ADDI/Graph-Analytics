"""Visualisations reseau des deux graphes (figures du rapport).

Sorties (outputs/) :
  - fig_ingredients.png : graphe d'ingredients, couleur = communaute Louvain,
    taille = force (somme des PMI), anneau noir + etiquette = ingredients « ponts »
    (coefficient de participation le plus eleve parmi les ingredients de degre >= 20)
  - fig_pays.png : graphe des pays, a gauche communautes Louvain,
    a droite regions de l'ONU (meme disposition pour comparer)

Pour la lisibilite, seules les aretes les plus fortes de chaque noeud sont
dessinees et servent a la disposition (squelette). Toutes les mesures du
rapport sont calculees sur le graphe complet.

Usage : python src/visualize.py
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
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
           "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295"]


def backbone(G, k):
    """Union des k aretes les plus fortes de chaque noeud (pour affichage)."""
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
    part = sorted(nx.community.louvain_communities(G, weight="weight", seed=SEED), key=len, reverse=True)
    comm = {n: i for i, c in enumerate(part) for n in c}
    pc = an.participation(G, part)
    strength = dict(G.degree(weight="weight"))

    B = backbone(G, 6)
    pos = nx.spring_layout(B, weight="weight", k=0.35, iterations=300, seed=SEED)

    bridges = [n for n in sorted((n for n in G if G.degree(n) >= 20), key=lambda n: pc[n], reverse=True)][:12]
    sizes = [30 + 3.0 * strength[n] for n in B]
    colors = [PALETTE[comm[n]] for n in B]

    fig, ax = plt.subplots(figsize=(15, 12))
    draw(ax, G, B, pos, colors, sizes)
    # anneau noir autour des ponts
    nx.draw_networkx_nodes(B, pos, nodelist=bridges, ax=ax, node_color="none",
                           node_size=[30 + 3.0 * strength[n] + 60 for n in bridges],
                           edgecolors="black", linewidths=1.8)
    hubs = []
    for i, c in enumerate(part[:6]):
        hubs += sorted(c, key=lambda n: strength[n], reverse=True)[:4]
    label(ax, pos, [n for n in dict.fromkeys(hubs) if n not in bridges], fs=9)
    label(ax, pos, bridges, fs=10, weight="bold")

    handles = []
    for i, c in enumerate(part[:6]):
        top = ", ".join(sorted(c, key=lambda n: strength[n], reverse=True)[:3])
        handles.append(plt.Line2D([], [], marker="o", ls="", color=PALETTE[i], ms=10,
                                  label=f"Communauté {i} ({len(c)}) : {top}"))
    handles.append(plt.Line2D([], [], marker="o", ls="", mfc="none", mec="black", mew=1.8, ms=11,
                              label="Ingrédient pont (participation élevée)"))
    ax.legend(handles=handles, loc="lower left", fontsize=10, frameon=True)
    ax.set_title(f"Graphe des ingrédients — {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes "
                 f"(affichage : {B.number_of_edges()} arêtes les plus fortes)\n"
                 "Source : CulinaryDB (CoSyLab, IIIT-Delhi)", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ingredients.png", dpi=150)
    plt.close(fig)
    print("fig_ingredients.png :", [n for n in bridges])


def fig_countries():
    prof = bg.load_country_profiles("all")
    G, _ = bg.build_country_graph(prof)
    geo = pd.read_csv(OUT / "geo_pays_communautes.csv").set_index("pays")
    comm = geo["communaute"].to_dict()
    region = geo["region"].to_dict()
    strength = dict(G.degree(weight="weight"))

    B = backbone(G, 5)
    # disposition sur la plus grande composante ; les pays isoles sont ranges en bas
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
    reg_names = {"Europe": "Europe", "Asia": "Asie", "Africa": "Afrique", "Americas": "Amériques", "Oceania": "Océanie"}

    fig, axes = plt.subplots(1, 2, figsize=(22, 10))
    draw(axes[0], G, B, pos, [PALETTE[comm[n]] for n in B], sizes, edge_alpha=0.10)
    draw(axes[1], G, B, pos, [reg_col[region[n]] for n in B], sizes, edge_alpha=0.10)

    big = sorted(set(comm.values()), key=lambda c: -sum(1 for v in comm.values() if v == c))[:6]
    hubs = []
    for c in big:
        members = [n for n in G if comm[n] == c and n in main]
        hubs += sorted(members, key=lambda n: strength[n], reverse=True)[:2]
    hubs = list(dict.fromkeys(hubs))
    span = max(ys) - min(ys)
    for ax in axes:
        label(ax, pos, hubs, fs=9)
        for n in rest:   # etiquettes sous les points pour ne pas les cacher
            ax.text(pos[n][0], pos[n][1] - 0.035 * span, SHORT.get(n, n), fontsize=8.5, ha="center", va="top")
        ax.text(min(xs), y0 + 0.06 * span, "Pays hors de la plus grande composante :",
                fontsize=9, style="italic", ha="left")
        ax.set_ylim(y0 - 0.12 * span, max(ys) + 0.05 * span)

    sizes_c = {c: sum(1 for v in comm.values() if v == c) for c in set(comm.values())}
    h0 = [plt.Line2D([], [], marker="o", ls="", color=PALETTE[c], ms=10,
                     label=f"Communauté {c} ({sizes_c[c]})") for c in big]
    axes[0].legend(handles=h0, loc="upper left", fontsize=10)
    h1 = [plt.Line2D([], [], marker="o", ls="", color=reg_col[r], ms=10, label=reg_names[r]) for r in regs]
    axes[1].legend(handles=h1, loc="upper left", fontsize=10)
    axes[0].set_title("Communautés détectées (Louvain)", fontsize=13)
    axes[1].set_title("Régions de l'ONU (même disposition)", fontsize=13)
    fig.suptitle(f"Graphe des pays — {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes (Jaccard ≥ {bg.JACCARD_THRESHOLD}) — "
                 f"affichage : {B.number_of_edges()} arêtes les plus fortes\n"
                 "Source : Wunderlich & Kohler (2022), EnviDat", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT / "fig_pays.png", dpi=130)
    plt.close(fig)
    print("fig_pays.png :", hubs)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_ingredients()
    fig_countries()
