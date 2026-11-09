"""Test whether country communities agree with UN regions beyond chance.

If communities had nothing to do with geography, randomly reshuffling the region labels should match the communities about as well as the real labels do.

Agreement is the sum of community majority counts divided by countries used.
Communities stay fixed during shuffling; countries without regions are excluded.
Community sizes and region counts use only countries with a known UN region.
Excluded countries are listed in stdout.

Usage: uv run python src/shuffle_test.py
"""
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42
N_SHUFFLES = 1000


def load_regions():
    dishes = pd.read_csv(ROOT / "data/raw/envidat/foodculture_dishes_rev2.csv",
                         sep=";", encoding="cp1252")
    dishes = dishes[dishes["country"].notna() & dishes["country"].str.strip().ne("")]
    codes = dishes.drop_duplicates("country").set_index("country")["iso3"]
    codes = codes.replace({"ZAR": "COD", "ROM": "ROU"})
    regions = pd.read_csv(ROOT / "data/raw/geography/un_regions_all.csv",
                          keep_default_na=False).set_index("alpha-3")["region"]
    return codes.map(regions).fillna("").to_dict()


def agreement(labels, groups):
    majority_total = sum(max(Counter(labels[i] for i in group).values(), default=0)
                         for group in groups)
    return majority_total / len(labels)


def community_table(labels, groups):
    rows = []
    for community, group in enumerate(groups):
        counts = Counter(labels[i] for i in group)
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        region, count = ordered[0] if ordered else ("", 0)
        rows.append({
            "community": community, "size": len(group), "majority_region": region,
            "majority_count": count, "majority_share": count / len(group) if group else 0,
            "regions": "; ".join(f"{name} {n}" for name, n in ordered),
        })
    return pd.DataFrame(rows)


def plot_null(null, observed):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(null, bins=20, color="#4c78a8", edgecolor="white", label="shuffled labels")
    ax.axvline(observed, color="#d62728", linewidth=2, label="real labels")
    ax.set_xlabel("Agreement with UN regions (share of countries)")
    ax.set_ylabel("Number of shuffles")
    ax.set_title("Communities and geography: shuffle test")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "shuffle_test.png", dpi=200)
    plt.close(fig)


def main():
    Gc, _ = bg.build_country_graph(bg.load_country_profiles())
    part = nx.community.louvain_communities(Gc, weight="weight", seed=SEED)
    part = sorted(part, key=lambda members: (-len(members), min(members)))
    community = {country: i for i, members in enumerate(part) for country in members}
    regions = load_regions()
    countries = [country for country in sorted(Gc) if regions.get(country)]
    excluded = sorted(set(Gc) - set(countries))
    labels = np.array([regions[country] for country in countries])
    groups = [[] for _ in part]
    for i, country in enumerate(countries):
        groups[community[country]].append(i)

    observed = agreement(labels, groups)
    rng = np.random.default_rng(SEED)
    null = np.array([agreement(rng.permutation(labels), groups) for _ in range(N_SHUFFLES)])
    p_value = (1 + np.count_nonzero(null >= observed)) / (1 + N_SHUFFLES)
    summary = {
        "n_countries": len(countries), "n_excluded": len(excluded),
        "n_communities": len(part), "observed_agreement": observed,
        "null_mean": null.mean(), "null_std": null.std(ddof=0),
        "null_p95": np.percentile(null, 95), "null_max": null.max(),
        "n_shuffles": N_SHUFFLES, "p_value": p_value,
    }
    table = community_table(labels, groups)
    OUT.mkdir(exist_ok=True)
    pd.DataFrame([summary]).to_csv(OUT / "shuffle_test.csv", encoding="utf-8", index=False)
    table.to_csv(OUT / "shuffle_communities.csv", encoding="utf-8", index=False)
    plot_null(null, observed)

    print(f"Countries used: {len(countries)}; excluded: {len(excluded)}")
    print(f"Excluded countries: {', '.join(excluded) or 'none'}")
    print(f"Communities: {len(part)}")
    print(f"Observed agreement: {observed:.6f}")
    print(f"Null ({N_SHUFFLES} shuffles): mean={null.mean():.6f}, "
          f"std={null.std(ddof=0):.6f}, p95={np.percentile(null, 95):.6f}, max={null.max():.6f}")
    print(f"p-value: {p_value:.6f}")
    print("\nPer-community region counts:")
    print(table.to_string(index=False, float_format=lambda value: f"{value:.3f}"))


if __name__ == "__main__":
    main()
