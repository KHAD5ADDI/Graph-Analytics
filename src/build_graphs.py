"""Construction des deux graphes du projet « The Hidden Bridges of World Cuisines ».

Graphe 1 (ingredients) : noeuds = ingredients, aretes = co-occurrence dans les
recettes de CulinaryDB, poids = PMI (association au-dela du hasard).
Graphe 2 (pays) : noeuds = pays, aretes = ingredients partages entre plats
nationaux (EnviDat), poids = similarite de Jaccard.

Sources a citer dans le rapport :
- CulinaryDB, CoSyLab, IIIT-Delhi (CC BY-NC-SA 3.0)
- Wunderlich & Kohler (2022), EnviDat, doi:10.16904/envidat.276 (ODbL)

Usage : python src/build_graphs.py
"""
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# --- Parametres de modelisation (a justifier dans le rapport) ---------------
MIN_RECIPES_PER_INGREDIENT = 50   # on ignore les ingredients trop rares
MIN_COOCCURRENCE = 10             # nb min de recettes communes pour une arete
PMI_THRESHOLD = 0.0               # on garde les associations > hasard
JACCARD_THRESHOLD = 0.30          # seuil du graphe des pays (voir outputs/sensibilite_pays.csv)
COUNTRY_PROFILE = "all"           # "national" (1 plat) ou "all" (tous les plats)


def read_csv(path, encoding="utf-8", **kw):
    return pd.read_csv(path, encoding=encoding, **kw)


# ---------------------------------------------------------------------------
# Graphe des ingredients
# ---------------------------------------------------------------------------
def load_culinarydb():
    d = RAW / "culinarydb"
    recipes = read_csv(d / "01_Recipe_Details.csv")
    pairs = read_csv(d / "04_Recipe-Ingredients_Aliases.csv")
    ing = read_csv(d / "02_Ingredients.csv")
    comp = read_csv(d / "03_Compound_Ingredients.csv")

    names = {}
    for _, r in ing.iterrows():
        names[int(r["Entity ID"])] = (r["Aliased Ingredient Name"].strip(), r["Category"], False)
    for _, r in comp.iterrows():
        names[int(r["entity_id"])] = (r["Compound Ingredient Name"].strip(), r["Category"], True)

    pairs = pairs.rename(columns={"Recipe ID": "recipe", "Entity ID": "entity"})
    pairs["entity"] = pairs["entity"].astype(int)
    pairs = pairs[["recipe", "entity"]].drop_duplicates()   # 456k -> 412k paires
    recipes = recipes.rename(columns={"Recipe ID": "recipe", "Cuisine": "region"})
    return recipes[["recipe", "region"]], pairs, names


def build_ingredient_graph(pairs, names, min_recipes=MIN_RECIPES_PER_INGREDIENT,
                           min_cooc=MIN_COOCCURRENCE, pmi_thr=PMI_THRESHOLD):
    n_recipes = pairs["recipe"].nunique()
    freq = pairs.groupby("entity")["recipe"].nunique()
    keep = freq[freq >= min_recipes].index.to_numpy()
    p = pairs[pairs["entity"].isin(keep)]

    r_idx = {r: i for i, r in enumerate(p["recipe"].unique())}
    e_idx = {e: i for i, e in enumerate(keep)}
    X = sparse.csr_matrix(
        (np.ones(len(p), dtype=np.int32),
         (p["recipe"].map(r_idx).to_numpy(), p["entity"].map(e_idx).to_numpy())),
        shape=(len(r_idx), len(keep)))
    C = (X.T @ X).tocoo()                                   # co-occurrences

    G = nx.Graph()
    for e in keep:
        name, cat, is_comp = names[int(e)]
        G.add_node(name, entity=int(e), category=cat, compound=is_comp,
                   n_recipes=int(freq[e]))
    fk = freq.loc[keep].to_numpy(dtype=float)
    for i, j, c in zip(C.row, C.col, C.data):
        if i >= j or c < min_cooc:
            continue
        pmi = np.log2(c * n_recipes / (fk[i] * fk[j]))
        if pmi > pmi_thr:
            G.add_edge(names[int(keep[i])][0], names[int(keep[j])][0],
                       weight=float(pmi), cooc=int(c))
    return G


# ---------------------------------------------------------------------------
# Graphe des pays
# ---------------------------------------------------------------------------
def load_country_profiles(mode=COUNTRY_PROFILE):
    # fichier EnviDat en cp1252 (un seul caractere accentue : Cote d'Ivoire)
    df = read_csv(RAW / "envidat" / "foodculture_dishes_rev2.csv", sep=";", encoding="cp1252")
    df = df[df["country"].notna() & (df["country"].str.strip() != "")]   # ligne vide
    ing_cols = list(df.columns[5:])
    df[ing_cols] = df[ing_cols].fillna(0).astype(float).clip(upper=1)   # corrige le '58'
    if mode == "national":
        df = df[df["national_dish"] == 1]
    prof = df.groupby("country")[ing_cols].max()
    return prof.astype(bool)


def build_country_graph(profiles, jaccard_thr=JACCARD_THRESHOLD):
    A = profiles.to_numpy(dtype=np.int32)
    inter = A @ A.T
    sizes = A.sum(axis=1)
    union = sizes[:, None] + sizes[None, :] - inter
    J = np.divide(inter, union, out=np.zeros(inter.shape), where=union > 0)

    G = nx.Graph()
    countries = list(profiles.index)
    for c, s in zip(countries, sizes):
        G.add_node(c, n_ingredients=int(s))
    for i in range(len(countries)):
        for j in range(i + 1, len(countries)):
            if J[i, j] >= jaccard_thr:
                G.add_edge(countries[i], countries[j], weight=float(J[i, j]),
                           shared=int(inter[i, j]))
    return G, J


# ---------------------------------------------------------------------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)

    recipes, pairs, names = load_culinarydb()
    Gi = build_ingredient_graph(pairs, names)
    nx.write_graphml(Gi, OUT / "ingredient_graph.graphml")
    print(f"Graphe ingredients : {Gi.number_of_nodes()} noeuds, {Gi.number_of_edges()} aretes")

    profiles = load_country_profiles()
    Gc, _ = build_country_graph(profiles)
    nx.write_graphml(Gc, OUT / "country_graph.graphml")
    print(f"Graphe pays ({COUNTRY_PROFILE}) : {Gc.number_of_nodes()} noeuds, {Gc.number_of_edges()} aretes")


if __name__ == "__main__":
    main()
