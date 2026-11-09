"""Measure figures (repository extras; the report uses its own tables).

Outputs (outputs/):
  - fig_centralites_ingredients.png / fig_centralites_pays.png: top 10 by hop betweenness
    (primary), by weighted betweenness with distance 1/weight (sensitivity: 1/PMI for
    ingredients, 1/Jaccard for countries) and by strength; bar colour = Louvain community
  - fig_degres.png: degree distribution of the two graphs

Values come from outputs/*_nodes.csv (written by analyze.py, full graphs).
Usage: python src/fig_mesures.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "outputs"
PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948",
           "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac", "#86bcb6", "#d37295"]
INK, MUTED, GRID = "#1d2024", "#6b7077", "#e4e2dc"
SHORT = {"Saint Vincent and the Grenadines": "St Vincent", "Lao People's Democratic Republic": "Laos",
         "Korea, Rep. of Korea": "Korea", "Bosnia and Herzegovina": "Bosnia", "Saint Kitts and Nevis": "St Kitts",
         "Micronesia (Federated States of)": "Micronesia", "Iran (Islamic Republic of)": "Iran",
         "Tanzania, United Rep. of": "Tanzania", "Antigua and Barbuda": "Antigua",
         "Republic of the Congo": "Congo", "United States of America": "USA"}

plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": INK, "axes.titlecolor": INK})


def load(name):
    df = pd.read_csv(OUT / f"{name}_nodes.csv", index_col=0, encoding="utf-8-sig")
    if name == "countries":   # same community numbers as fig_pays.png
        geo = pd.read_csv(OUT / "geo_pays_communautes.csv", encoding="utf-8-sig").set_index("country")
        df["community"] = geo["community"]
    return df


def bar_panel(ax, s, comm, title, fmt):
    s = s.dropna().sort_values().tail(10)
    cols = [PALETTE[comm[n] % len(PALETTE)] for n in s.index]
    ax.barh(range(len(s)), s.values, color=cols, height=0.7, edgecolor="white", linewidth=1)
    ax.set_yticks(range(len(s)), [SHORT.get(n, n) for n in s.index])
    for i, v in enumerate(s.values):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=8.5, color=MUTED)
    ax.set_xlim(0, s.max() * 1.22)
    ax.set_title(title, fontsize=11, loc="left", fontweight="bold")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)


def fig_centralities(name, label, source, weight_name, weight_label):
    df = load(name)
    comm = df["community"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
    bar_panel(axes[0], df["betweenness_hop"], comm,
              "Hop betweenness\n(primary: every edge is one step)", "{:.3f}")
    bar_panel(axes[1], df[f"betweenness_{weight_name}"], comm,
              f"Betweenness with distance 1/{weight_label}\n(sensitivity: stronger link = shorter step)", "{:.3f}")
    bar_panel(axes[2], df["strength"], comm, "Strength\n(sum of edge weights)", "{:.1f}")
    n_comm = comm.nunique()
    handles = [plt.Line2D([], [], marker="s", ls="", color=PALETTE[i], ms=9, label=f"Community {i}")
               for i in range(min(n_comm, 7))]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles), frameon=False, fontsize=9.5)
    fig.suptitle(f"{label}: top 10 by centrality, colour = Louvain community\nSource: {source}",
                 fontsize=13, color=INK)
    fig.tight_layout(rect=(0, 0.06, 1, 0.92))
    fig.savefig(OUT / f"fig_centralites_{'pays' if name == 'countries' else name}.png", dpi=150)
    plt.close(fig)


def fig_degrees():
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, name, label in [(axes[0], "ingredients", "Ingredients"), (axes[1], "countries", "Countries")]:
        d = load(name)["degree"]
        ax.hist(d, bins=30, color="#4e79a7", edgecolor="white", linewidth=1)
        ax.axvline(d.mean(), color=INK, lw=1.2, ls="--")
        ax.text(d.mean(), ax.get_ylim()[1] * 0.95, f"  mean {d.mean():.1f}", fontsize=9, color=INK, va="top")
        ax.set_title(f"{label} ({len(d)} nodes)", loc="left", fontweight="bold", fontsize=11)
        ax.set_xlabel("Degree (number of neighbours)")
        ax.set_ylabel("Number of nodes")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.suptitle("Degree distributions", fontsize=13, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig_degres.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_centralities("ingredients", "Ingredient graph", "CulinaryDB (CoSyLab, IIIT-Delhi)", "pmi", "PMI")
    fig_centralities("countries", "Country graph", "Wunderlich & Kohler (2022), EnviDat", "jaccard", "Jaccard")
    fig_degrees()
    print("fig_centralites_ingredients.png, fig_centralites_pays.png, fig_degres.png")
