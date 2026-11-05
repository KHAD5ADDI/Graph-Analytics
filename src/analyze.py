"""Mesures exigees par le sujet + Louvain + coefficient de participation
+ analyse de sensibilite aux seuils.

Conventions (a rappeler dans le rapport) :
- diametre et rayon : plus grande composante connexe, graphe NON pondere (sauts)
- intermediarite : distance = 1 / poids (un poids fort = proximite)
- Louvain : graphe pondere, graine fixee (seed=42)
- coefficient de participation : P_i = 1 - sum_c (k_ic / k_i)^2 (Guimera & Amaral)

Usage : python src/analyze.py
"""
from pathlib import Path

import networkx as nx
import pandas as pd

import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42


def participation(G, part):
    comm = {n: i for i, c in enumerate(part) for n in c}
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


def global_measures(G):
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    lcc = G.subgraph(comps[0])
    part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
    return {
        "noeuds": G.number_of_nodes(),
        "aretes": G.number_of_edges(),
        "densite": round(nx.density(G), 4),
        "composantes": len(comps),
        "taille_LCC": lcc.number_of_nodes(),
        "diametre_LCC": nx.diameter(lcc) if lcc.number_of_nodes() > 1 else 0,
        "rayon_LCC": nx.radius(lcc) if lcc.number_of_nodes() > 1 else 0,
        "clustering_moyen": round(nx.average_clustering(G), 3),
        "communautes_Louvain": len(part),
        "modularite": round(nx.community.modularity(G, part, weight="weight"), 3),
    }, part


def node_table(G, part):
    H = G.copy()
    for u, v, d in H.edges(data=True):
        d["dist"] = 1.0 / d["weight"]
    comm = {n: i for i, c in enumerate(part) for n in c}
    part_coef = participation(G, part)
    bet = nx.betweenness_centrality(H, weight="dist")
    # vecteur propre : defini sur la plus grande composante connexe uniquement
    lcc = G.subgraph(max(nx.connected_components(G), key=len))
    eig = nx.eigenvector_centrality_numpy(lcc, weight="weight")
    df = pd.DataFrame({
        "degre": dict(G.degree()),
        "force": dict(G.degree(weight="weight")),
        "intermediarite": bet,
        "vecteur_propre": eig,
        "communaute": comm,
        "participation": part_coef,
    })
    return df.sort_values("intermediarite", ascending=False)


def sensitivity_ingredients(pairs, names):
    rows = []
    for min_cooc in (5, 10, 20, 50):
        for pmi in (0.0, 0.5, 1.0):
            G = bg.build_ingredient_graph(pairs, names, min_cooc=min_cooc, pmi_thr=pmi)
            m, _ = global_measures(G)
            rows.append({"min_cooc": min_cooc, "seuil_PMI": pmi, **m})
    return pd.DataFrame(rows)


def sensitivity_countries(mode):
    prof = bg.load_country_profiles(mode)
    rows = []
    for thr in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
        G, _ = bg.build_country_graph(prof, jaccard_thr=thr)
        m, _ = global_measures(G)
        rows.append({"profil": mode, "seuil_Jaccard": thr, **m})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)

    # --- Graphe des ingredients ---
    recipes, pairs, names = bg.load_culinarydb()
    Gi = bg.build_ingredient_graph(pairs, names)
    mi, part_i = global_measures(Gi)
    ti = node_table(Gi, part_i)
    ti.to_csv(OUT / "ingredients_nodes.csv", encoding="utf-8-sig")
    print("== INGREDIENTS ==")
    print(mi)
    print("\nTop 10 intermediarite :\n", ti.head(10).round(3))
    print("\nTop 10 participation (ponts) parmi ingredients degre>=20 :\n",
          ti[ti.degre >= 20].sort_values("participation", ascending=False).head(10).round(3))
    for k, c in enumerate(sorted(part_i, key=len, reverse=True)[:6]):
        top = sorted(c, key=lambda n: Gi.degree(n, weight="weight"), reverse=True)[:8]
        print(f"communaute {k} ({len(c)}):", ", ".join(top))

    s_i = sensitivity_ingredients(pairs, names)
    s_i.to_csv(OUT / "sensibilite_ingredients.csv", index=False)
    print("\nSensibilite ingredients :\n", s_i)

    # --- Graphe des pays ---
    print("\n== PAYS ==")
    for mode in ("all", "national"):
        prof = bg.load_country_profiles(mode)
        Gc, _ = bg.build_country_graph(prof)
        mc, part_c = global_measures(Gc)
        print(f"\nprofil={mode} (seuil Jaccard {bg.JACCARD_THRESHOLD}):", mc)
        if mode == bg.COUNTRY_PROFILE:
            tc = node_table(Gc, part_c)
            tc.to_csv(OUT / "countries_nodes.csv", encoding="utf-8-sig")
            print("Top 10 intermediarite :\n", tc.head(10).round(3))
            for k, c in enumerate(sorted(part_c, key=len, reverse=True)):
                print(f"communaute {k} ({len(c)}):", ", ".join(sorted(c)[:14]))
    s_c = pd.concat([sensitivity_countries("all"), sensitivity_countries("national")])
    s_c.to_csv(OUT / "sensibilite_pays.csv", index=False)
    print("\nSensibilite pays :\n", s_c)


if __name__ == "__main__":
    main()
