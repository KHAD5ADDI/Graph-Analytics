"""Extra check of ingredient communities against CulinaryDB cuisine labels.

This is backup material for the oral, not an analysis used in the report.
Ratios count distinct (recipe, graph ingredient) occurrences; the shuffle test
keeps each recipe's dominant community fixed and permutes its cuisine label.

Usage (from src/): UV_NO_CACHE=1 uv run python cuisine_check.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import analyze as an
import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42
N_SHUFFLES = 1000
MIN_RECIPES = 200
# Descriptions of the strongest ingredients, not inferred cuisine identities.
COMMUNITY_LABELS = [
    "0 vegetables,\nherbs", "1 sweet,\nbaking", "2 salad,\nsauce, beef",
    "3 ginger,\nsoy, fish", "4 spices,\nlegumes",
]


def recipe_community_counts(recipes, pairs, G, part):
    community = an.community_map(part)
    entity_community = {data["entity"]: community[name]
                        for name, data in G.nodes(data=True)}
    # Use the actual graph entity IDs: other IDs can have the same name.
    occurrences = pairs[pairs["entity"].isin(entity_community)].copy()
    occurrences = occurrences.drop_duplicates(["recipe", "entity"])
    occurrences["community"] = occurrences["entity"].map(entity_community)
    kept = recipes[recipes["recipe"].isin(occurrences["recipe"])].copy()
    kept = kept.sort_values("recipe").reset_index(drop=True)
    assert kept["recipe"].is_unique, "Recipe metadata must have unique IDs"
    assert kept["region"].notna().all(), "Kept recipes must have cuisine labels"
    assert occurrences["recipe"].nunique() == len(kept), "Missing recipe metadata"
    counts = pd.crosstab(occurrences["recipe"], occurrences["community"])
    counts = counts.reindex(index=kept["recipe"], columns=range(len(part)), fill_value=0)
    return kept, counts.to_numpy(dtype=np.int64)


def ratio_table(recipes, counts):
    occurrences = pd.DataFrame(counts)
    occurrences["cuisine"] = recipes["region"].to_numpy()
    observed = occurrences.groupby("cuisine", sort=True).sum()
    n_recipes = recipes.groupby("region").size()
    shares = observed.sum(axis=0) / observed.to_numpy().sum()
    expected = observed.sum(axis=1).to_numpy()[:, None] * shares.to_numpy()
    ratios = observed.to_numpy() / expected
    # A zero observed count has ratio 0 and log2 ratio -inf, without smoothing.
    with np.errstate(divide="ignore"):
        log_ratios = np.log2(ratios)
    rows = []
    for i, cuisine in enumerate(observed.index):
        for k in observed.columns:
            rows.append({
                "cuisine": cuisine, "n_recipes": int(n_recipes[cuisine]),
                "community": k, "observed": int(observed.iloc[i, k]),
                "expected": expected[i, k], "ratio": ratios[i, k],
                "log2_ratio": log_ratios[i, k],
            })
    return pd.DataFrame(rows)


def top_table(ratios):
    eligible = ratios[ratios["n_recipes"] >= MIN_RECIPES]
    rows = []
    for community, group in eligible.groupby("community", sort=True):
        for kind, ascending, n in (("top", False, 5), ("bottom", True, 3)):
            selected = group.sort_values(
                ["ratio", "cuisine"], ascending=[ascending, True]).head(n)
            for rank, row in enumerate(selected.itertuples(index=False), start=1):
                rows.append({
                    "community": community, "kind": kind, "rank": rank,
                    "cuisine": row.cuisine, "ratio": row.ratio,
                    "n_recipes": row.n_recipes,
                })
    return pd.DataFrame(rows)


def agreement(dominant, cuisines, n_cuisines, n_communities):
    counts = np.bincount(cuisines * n_communities + dominant,
                         minlength=n_cuisines * n_communities)
    return counts.reshape(n_cuisines, n_communities).max(axis=1).sum() / len(dominant)


def shuffle_test(recipes, counts):
    # Columns are communities in index order, so argmax resolves ties downward.
    dominant = counts.argmax(axis=1)
    labels, cuisines = np.unique(recipes["region"].to_numpy(), return_inverse=True)
    n_cuisines, n_communities = len(labels), counts.shape[1]
    observed = agreement(dominant, cuisines, n_cuisines, n_communities)
    rng = np.random.default_rng(SEED)
    null = np.array([
        agreement(dominant, rng.permutation(cuisines), n_cuisines, n_communities)
        for _ in range(N_SHUFFLES)
    ])
    baseline = np.bincount(dominant, minlength=n_communities).max() / len(dominant)
    return {
        "n_recipes": len(recipes), "n_cuisines": n_cuisines,
        "observed": observed, "null_mean": null.mean(),
        "null_std": null.std(ddof=0), "null_max": null.max(),
        "baseline_majority": baseline,
        "p_value": (1 + np.count_nonzero(null >= observed)) / (1 + N_SHUFFLES),
    }


def plot_heatmap(ratios, path):
    eligible = ratios[ratios["n_recipes"] >= MIN_RECIPES]
    matrix = eligible.pivot(index="cuisine", columns="community", values="ratio")
    matrix = matrix.reindex(columns=range(len(COMMUNITY_LABELS)))
    values = matrix.to_numpy()
    # Put the same strongest community together, then highest ratios first.
    order = np.lexsort((matrix.index.to_numpy(), -values.max(axis=1),
                        values.argmax(axis=1)))
    matrix = matrix.iloc[order]
    with np.errstate(divide="ignore"):
        log_ratios = np.log2(matrix.to_numpy())
    finite = log_ratios[np.isfinite(log_ratios)]
    limit = max(float(np.abs(finite).max()), 1e-6)
    # If a zero occurs, show -inf at the negative colour limit; do not smooth it.
    colours = np.clip(log_ratios, -limit, limit)
    n_recipes = eligible.drop_duplicates("cuisine").set_index("cuisine")["n_recipes"]

    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
    im = ax.imshow(colours, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks(range(len(COMMUNITY_LABELS)), COMMUNITY_LABELS, fontsize=12)
    ax.set_yticks(range(len(matrix)),
                  [f"{cuisine} (n={n_recipes[cuisine]:,})" for cuisine in matrix.index],
                  fontsize=11)
    ax.tick_params(length=0, pad=8)
    ax.set_title("Ingredient communities vs cuisine labels (observed / expected)",
                 fontsize=16, pad=16)
    for i in range(len(matrix)):
        for k in range(len(COMMUNITY_LABELS)):
            colour = "white" if abs(colours[i, k]) > .6 * limit else "black"
            ax.text(k, i, f"{matrix.iloc[i, k]:.2f}", ha="center", va="center",
                    fontsize=11, color=colour)
    colourbar = fig.colorbar(im, ax=ax, fraction=.035, pad=.025)
    colourbar.set_label("log2(observed / expected)", fontsize=12)
    colourbar.ax.tick_params(labelsize=11)
    fig.subplots_adjust(left=.24, right=.93, bottom=.12, top=.91)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def print_summary(G, part, recipes, counts, top, summary):
    print(f"Ingredient graph: {len(G)} ingredients; {len(part)} communities")
    print("Partition matches outputs/brokers_ingredients.csv for every ingredient.")
    print(f"Kept recipes: {len(recipes):,}; cuisine labels: {summary['n_cuisines']}")
    print(f"Distinct (recipe, graph ingredient) occurrences: {counts.sum():,}")
    print(f"\nPer-community cuisines (at least {MIN_RECIPES} kept recipes; ratio, n_recipes):")
    for k in range(len(part)):
        print("  " + COMMUNITY_LABELS[k].replace("\n", " "))
        for kind in ("top", "bottom"):
            selected = top[(top["community"] == k) & (top["kind"] == kind)]
            entries = "; ".join(f"{row.cuisine} ({row.ratio:.2f}, n={row.n_recipes:,})"
                                for row in selected.itertuples(index=False))
            print(f"    {kind.capitalize()}: {entries}")
    print(f"\nObserved agreement: {summary['observed']:.6f}")
    print(f"Null ({N_SHUFFLES} cuisine-label shuffles, seed {SEED}): "
          f"mean={summary['null_mean']:.6f}, std={summary['null_std']:.6f}, "
          f"max={summary['null_max']:.6f}")
    print(f"p-value: {summary['p_value']:.6f}")
    majority = np.bincount(counts.argmax(axis=1), minlength=len(part)).argmax()
    print(f"Trivial majority baseline (community {majority}): "
          f"{summary['baseline_majority']:.6f}")
    print(f"Observed minus baseline: "
          f"{100 * (summary['observed'] - summary['baseline_majority']):.2f} percentage points")
    print("Baseline caveat: the overall dominant community already accounts for "
          f"{summary['baseline_majority']:.1%} of recipes; high agreement alone "
          "does not show a cuisine match.")
    sizes = recipes["region"].value_counts()
    print(f"Sampling caveat: USA n={sizes.get('USA', 0):,}; "
          f"Italy n={sizes.get('Italy', 0):,}; ratios and the shuffle test use "
          "this imbalanced sample.")
    print("Extra check for the oral; not used in the report.")


def main():
    recipes, pairs, names = bg.load_culinarydb()
    G = bg.build_ingredient_graph(pairs, names)
    part = an.louvain_partition(G)
    community = an.community_map(part)
    reference = pd.read_csv(OUT / "brokers_ingredients.csv")
    assert reference["ingredient"].is_unique, "Duplicate ingredients in broker table"
    assert community == reference.set_index("ingredient")["community"].to_dict(), \
        "Ingredient community assignments differ from brokers_ingredients.csv"
    assert len(G) == 362 and len(part) == 5, "Expected 362 ingredients in five communities"

    recipes, counts = recipe_community_counts(recipes, pairs, G, part)
    ratios = ratio_table(recipes, counts)
    top = top_table(ratios)
    summary = shuffle_test(recipes, counts)
    OUT.mkdir(exist_ok=True)
    ratios.to_csv(OUT / "cuisine_community_ratio.csv", encoding="utf-8", index=False)
    top.to_csv(OUT / "cuisine_community_top.csv", encoding="utf-8", index=False)
    pd.DataFrame([summary]).to_csv(OUT / "cuisine_shuffle_test.csv",
                                  encoding="utf-8", index=False)
    plot_heatmap(ratios, OUT / "cuisine_community_heatmap.png")
    print_summary(G, part, recipes, counts, top, summary)


if __name__ == "__main__":
    main()
