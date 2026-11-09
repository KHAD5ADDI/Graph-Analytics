"""Extend the broker analysis without changing existing scripts or outputs.

Usage (from src/): UV_NO_CACHE=1 uv run python brokers_extra.py
"""
from collections import Counter

import networkx as nx
import pandas as pd
from scipy.stats import spearmanr

import analyze as an
import brokers
import build_graphs as bg
import shuffle_test

OUT = brokers.OUT


def checked_partitions(Gi, Gc):
    """Check seed-42 community numbering against the existing CSV outputs."""
    part_i = an.louvain_partition(Gi)
    part_c = an.louvain_partition(Gc)
    ingredients = pd.read_csv(OUT / "brokers_ingredients.csv")
    assert an.community_map(part_i) == ingredients.set_index(
        "ingredient")["community"].to_dict(), "Ingredient communities changed"

    regions = shuffle_test.load_regions()
    countries = [country for country in sorted(Gc) if regions.get(country)]
    community = an.community_map(part_c)
    groups = [[] for _ in part_c]
    for i, country in enumerate(countries):
        groups[community[country]].append(i)
    labels = [regions[country] for country in countries]
    actual = shuffle_test.community_table(labels, groups)
    expected = pd.read_csv(OUT / "shuffle_communities.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(actual, expected, check_exact=False,
                                  rtol=1e-14, atol=0)
    # The shuffle CSV has region counts, not country identities. Check those
    # against the saved node table as well, so a swapped membership cannot pass.
    saved = pd.read_csv(OUT / "countries_nodes.csv")
    assert community == saved.set_index("node")["community"].to_dict(), (
        "Country communities changed")
    return part_i, part_c, regions


def country_table(G, part, regions):
    community = an.community_map(part)
    hop = nx.betweenness_centrality(G)
    rows = []
    for country in G:
        degree = G.degree(country)
        outside = sum(community[nb] != community[country] for nb in G[country])
        rows.append({
            "country": country, "region": regions.get(country, ""),
            "community": community[country], "degree": degree,
            "strength": G.degree(country, weight="weight"),
            "betweenness_hop": hop[country], "neighbours_outside": outside,
            "share_outside": outside / degree if degree else float("nan"),
        })
    table = pd.DataFrame(rows)
    table["rank_hop"] = table["betweenness_hop"].rank(
        ascending=False, method="min").astype(int)
    table = table.sort_values(["betweenness_hop", "country"], ascending=[False, True])
    table["outside_regions"] = ""
    for index in table.head(10).index:
        country = table.at[index, "country"]
        counts = Counter(regions.get(nb, "") or "Unknown" for nb in G[country]
                         if community[nb] != community[country])
        table.at[index, "outside_regions"] = "; ".join(
            f"{region} {count}" for region, count in
            sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return table[["country", "region", "community", "degree", "strength",
                  "betweenness_hop", "rank_hop", "neighbours_outside",
                  "share_outside", "outside_regions"]]


def beyond_degree_table(table):
    result = table[["ingredient", "frequency", "community", "degree",
                    "betweenness_hop", "rank_hop"]].copy()
    result["rank_degree"] = result["degree"].rank(
        ascending=False, method="min").astype(int)
    result["rank_gap"] = result["rank_degree"] - result["rank_hop"]
    result["share_outside"] = table["neighbours_outside"] / table["degree"].replace(0, float("nan"))
    result["in_top50_hop"] = result["rank_hop"] <= 50
    return result[["in_top50_hop", "ingredient", "frequency", "community", "degree",
                   "rank_degree", "betweenness_hop", "rank_hop", "rank_gap",
                   "share_outside"]].sort_values(
        ["rank_gap", "ingredient"], ascending=[False, True])


def distance_table(G, table):
    H = G.copy()
    for _, _, data in H.edges(data=True):
        data["distance_inv1p"] = 1.0 / (1.0 + data["weight"])
    inv1p = nx.betweenness_centrality(H, weight="distance_inv1p")
    result = table[["ingredient", "frequency", "rank_pmi", "rank_hop"]].copy()
    result = result.rename(columns={"rank_pmi": "rank_inv"})
    result["betweenness_inv1p"] = result["ingredient"].map(inv1p)
    result["rank_inv1p"] = result["betweenness_inv1p"].rank(
        ascending=False, method="min").astype(int)
    return result[["ingredient", "frequency", "betweenness_inv1p", "rank_inv1p",
                   "rank_inv", "rank_hop"]].sort_values(["rank_inv1p", "ingredient"])


def summary_table(G, ingredients, countries, distances):
    lcc = G.subgraph(max(nx.connected_components(G), key=len))
    # Each unordered pair is counted once, without the source-to-itself path.
    lengths = Counter(distance for source, paths in nx.all_pairs_shortest_path_length(lcc)
                      for target, distance in paths.items() if source < target)
    n_pairs = len(lcc) * (len(lcc) - 1) // 2
    assert sum(lengths.values()) == n_pairs
    weights = [data["weight"] for _, _, data in G.edges(data=True)]
    top_inv = set(ingredients.sort_values(
        ["betweenness_pmi", "ingredient"], ascending=[False, True]).head(10)["ingredient"])
    top_hop = set(ingredients.sort_values(
        ["betweenness_hop", "ingredient"], ascending=[False, True]).head(10)["ingredient"])
    top_inv1p = set(distances.head(10)["ingredient"])
    rows = {
        "n_pairs_largest_component_ingredients": n_pairs,
        "share_pairs_1_hop": lengths[1] / n_pairs,
        "share_pairs_2_hops": lengths[2] / n_pairs,
        "share_pairs_3_hops": lengths[3] / n_pairs,
        "rho_hop_betweenness_degree": spearmanr(
            ingredients["betweenness_hop"], ingredients["degree"]).statistic,
        "rho_frequency_inv1p": spearmanr(
            distances["frequency"], distances["betweenness_inv1p"]).statistic,
        "rho_inv_inv1p": spearmanr(distances["rank_inv"], distances["rank_inv1p"]).statistic,
        "rho_hop_inv1p": spearmanr(distances["rank_hop"], distances["rank_inv1p"]).statistic,
        "top10_overlap_inv_inv1p": len(top_inv & top_inv1p),
        "top10_overlap_hop_inv1p": len(top_hop & top_inv1p),
        "pmi_min": min(weights), "pmi_max": max(weights),
        "distance_inv_max": 1.0 / min(weights),
        "distance_inv1p_min": 1.0 / (1.0 + max(weights)),
        "distance_inv1p_max": 1.0 / (1.0 + min(weights)),
        "rho_country_betweenness_degree": spearmanr(
            countries["betweenness_hop"], countries["degree"]).statistic,
    }
    return pd.DataFrame(rows.items(), columns=["measure", "value"])


def main():
    recipes, pairs, names = bg.load_culinarydb()
    Gi = bg.build_ingredient_graph(pairs, names)
    Gc, _ = bg.build_country_graph(bg.load_country_profiles())
    part_i, part_c, regions = checked_partitions(Gi, Gc)
    ingredients, part_brokers = brokers.ingredient_table(Gi)
    assert part_i == part_brokers, "Broker communities differ from analyze"
    assert len(Gi) == 362 and len(Gc) == 171, "Graph sizes changed"
    countries = country_table(Gc, part_c, regions)
    beyond = beyond_degree_table(ingredients)
    distances = distance_table(Gi, ingredients)
    summary = summary_table(Gi, ingredients, countries, distances)
    OUT.mkdir(exist_ok=True)
    for name, frame in (("countries", countries), ("beyond_degree", beyond),
                        ("distance", distances), ("summary", summary)):
        frame.to_csv(OUT / f"brokers_extra_{name}.csv", encoding="utf-8", index=False)

    print(f"Ingredients: {len(Gi)} nodes, {Gi.number_of_edges()} edges")
    print(f"Countries: {len(Gc)} nodes, {Gc.number_of_edges()} edges")
    print("Community checks passed: brokers_ingredients.csv, "
          "shuffle_communities.csv and countries_nodes.csv")
    for title, frame in (("Countries by hop betweenness", countries),
                         ("Ingredients by rank gap (all ingredients)", beyond),
                         ("Ingredients by rank gap within the hop top 50",
                          beyond[beyond["in_top50_hop"]]),
                         ("Ingredients by 1/(1+PMI) betweenness", distances)):
        print(f"\nTop 10: {title}:")
        print(frame.head(10).to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nSummary (full precision is saved in brokers_extra_summary.csv):")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.12g}"))


if __name__ == "__main__":
    main()
