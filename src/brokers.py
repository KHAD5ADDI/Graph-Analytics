"""Compare ingredient brokers and inspect connectivity in both cuisine graphs.

Hop betweenness is the primary measure; inverse-PMI distance is a sensitivity check.
Usage: uv run python src/brokers.py
"""
from pathlib import Path

import networkx as nx
import pandas as pd
from scipy.stats import spearmanr

import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42


def ingredient_table(G):
    part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
    part = sorted(part, key=lambda c: (-len(c), min(c)))
    community = {n: i for i, c in enumerate(part) for n in c}
    hop = nx.betweenness_centrality(G)
    H = G.copy()
    for _, _, data in H.edges(data=True):
        # a stronger association means a shorter step
        data["distance"] = 1.0 / data["weight"]
    pmi = nx.betweenness_centrality(H, weight="distance")

    rows = []
    for n, data in G.nodes(data=True):
        inside = sum(community[nb] == community[n] for nb in G[n])
        rows.append({
            "ingredient": n, "category": data["category"],
            "frequency": data["n_recipes"], "degree": G.degree(n),
            "strength": G.degree(n, weight="weight"),
            "betweenness_hop": hop[n], "betweenness_pmi": pmi[n],
            "community": community[n], "neighbours_inside": inside,
            "neighbours_outside": G.degree(n) - inside,
        })
    table = pd.DataFrame(rows)
    # Equal centralities share the highest rank occupied by the tie.
    for measure in ("hop", "pmi"):
        table[f"rank_{measure}"] = table[f"betweenness_{measure}"].rank(
            ascending=False, method="min").astype(int)
    columns = ["ingredient", "category", "frequency", "degree", "strength",
               "betweenness_hop", "betweenness_pmi", "rank_hop", "rank_pmi",
               "community", "neighbours_inside", "neighbours_outside"]
    table = table[columns].sort_values(
        ["betweenness_hop", "ingredient"], ascending=[False, True])
    return table, part


def spearman_table(table):
    rows = []
    for y in ("betweenness_hop", "betweenness_pmi", "degree"):
        rho, p_value = spearmanr(table["frequency"], table[y])
        rows.append({"graph": "ingredients", "x": "frequency", "y": y,
                     "rho": rho, "p_value": p_value, "n": len(table)})
    return pd.DataFrame(rows)


def inspected_table(G, table):
    top_pmi = table.sort_values(
        ["betweenness_pmi", "ingredient"], ascending=[False, True])
    selected = set(table.head(3)["ingredient"]) | set(top_pmi.head(3)["ingredient"])
    inspected = table[table["ingredient"].isin(selected)].copy()
    community = table.set_index("ingredient")["community"].to_dict()
    neighbours = []
    for n in inspected["ingredient"]:
        top = sorted(G[n], key=lambda nb: (-G[n][nb]["weight"], nb))[:5]
        neighbours.append("; ".join(
            f"{nb} (PMI {G[n][nb]['weight']:.2f}, community {community[nb]})"
            for nb in top))
    inspected["top_neighbours"] = neighbours
    return inspected


def connectivity_tables(graphs):
    cuts, components = [], []
    for label, G in graphs.items():
        for n in sorted(nx.articulation_points(G)):
            cuts.append({"graph": label, "kind": "articulation_point", "item": n})
        bridges = sorted(tuple(sorted(edge)) for edge in nx.bridges(G))
        for u, v in bridges:
            cuts.append({"graph": label, "kind": "bridge", "item": f"{u} -- {v}"})
        groups = sorted(nx.connected_components(G), key=lambda c: (-len(c), min(c)))
        for i, group in enumerate(groups):
            members = (f"(largest component, {len(group)} nodes)" if len(group) >= 20
                       else "; ".join(sorted(group)))
            components.append({"graph": label, "component": i,
                               "size": len(group), "members": members})
    return (pd.DataFrame(cuts, columns=["graph", "kind", "item"]),
            pd.DataFrame(components, columns=["graph", "component", "size", "members"]))


def print_summary(graphs, table, part, correlations, inspected, cuts, components):
    for label, G in graphs.items():
        print(f"{label.capitalize()} graph: {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
    modularity = nx.community.modularity(graphs["ingredients"], part, weight="weight")
    print(f"Ingredient Louvain: {len(part)} communities, modularity = {modularity:.6f}")
    print("\nSpearman correlations (ingredients):")
    for row in correlations.itertuples(index=False):
        print(f"  {row.x} vs {row.y}: rho = {row.rho:.6f}, "
              f"p_value = {row.p_value:.6g}, n = {row.n}")

    hop = table.head(10).reset_index(drop=True)
    pmi = table.sort_values(
        ["betweenness_pmi", "ingredient"], ascending=[False, True]).head(10)
    comparison = pd.DataFrame({
        "hop_ingredient": hop["ingredient"], "betweenness_hop": hop["betweenness_hop"],
        "pmi_ingredient": pmi["ingredient"].to_numpy(),
        "betweenness_pmi": pmi["betweenness_pmi"].to_numpy(),
    })
    print("\nTop 10: hop (primary) and 1/PMI (sensitivity), highest first:")
    print(comparison.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    print("\nInspected ingredients (union of both top threes):")
    for row in inspected.itertuples(index=False):
        print(f"  {row.ingredient}: community {row.community}, "
              f"neighbours inside = {row.neighbours_inside}, outside = {row.neighbours_outside}")
        print(f"    {row.top_neighbours}")

    print("\nCut points:")
    for label in graphs:
        for kind in ("articulation_point", "bridge"):
            items = cuts.loc[(cuts["graph"] == label) & (cuts["kind"] == kind), "item"]
            print(f"  {label} {kind} ({len(items)}): " + ("; ".join(items) or "none"))
    print("\nConnected components:")
    for label in graphs:
        subset = components[components["graph"] == label]
        print(f"  {label}: {len(subset)} components, largest = {subset['size'].max()} nodes")
        for row in subset.itertuples(index=False):
            print(f"    component {row.component}, size {row.size}: {row.members}")


def main():
    recipes, pairs, names = bg.load_culinarydb()
    Gi = bg.build_ingredient_graph(pairs, names)
    Gc, _ = bg.build_country_graph(bg.load_country_profiles())
    graphs = {"ingredients": Gi, "countries": Gc}
    table, part = ingredient_table(Gi)
    correlations = spearman_table(table)
    inspected = inspected_table(Gi, table)
    cuts, components = connectivity_tables(graphs)
    OUT.mkdir(exist_ok=True)
    for name, frame in (("ingredients", table), ("spearman", correlations),
                        ("inspected", inspected), ("cut_points", cuts),
                        ("components", components)):
        frame.to_csv(OUT / f"brokers_{name}.csv", encoding="utf-8", index=False)
    print_summary(graphs, table, part, correlations, inspected, cuts, components)


if __name__ == "__main__":
    main()
