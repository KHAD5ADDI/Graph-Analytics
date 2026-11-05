"""Proximite culinaire vs geographie (objectif 3 du projet).

Sources a citer :
- Wunderlich & Kohler (2022), EnviDat, doi:10.16904/envidat.276 (ODbL) :
  plats nationaux + variables de gravite (distance, frontiere, langue, colonie)
- UN M49 regions : depot lukes/ISO-3166-Countries-with-Regional-Codes (GitHub)

Analyses :
  1. Les communautes Louvain recoupent-elles les regions de l'ONU ?
     (NMI / ARI + test de permutation)
  2. La similarite culinaire (Jaccard) decroit-elle avec la distance ?
     (Spearman, regression OLS avec frontiere / langue / colonie / meme region)
  3. Connexions inattendues : paires tres proches culinairement mais lointaines,
     et pays dont la communaute ne correspond pas a leur region.
  4. Validation : notre Jaccard vs les similarites des auteurs (Manhattan, LSA).

Usage : python src/geography.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

import analyze as an
import build_graphs as bg

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / "data" / "raw" / "geography"
OUT = ROOT / "outputs"
SEED = 42
N_PERM = 2000


def load_iso3():
    df = bg.read_csv(bg.RAW / "envidat" / "foodculture_dishes_rev2.csv", sep=";", encoding="cp1252")
    df = df[df["country"].notna() & (df["country"].str.strip() != "")]
    return df.drop_duplicates("country").set_index("country")["iso3"]


def load_pairs():
    cols = ["i_iso3", "j_iso3", "dist", "distcap", "contig", "comlang_off", "colony",
            "comcol", "food_sim_manhattan", "food_sim_lsa"]
    g = pd.read_csv(GEO / "gravity_food_sim_final.csv", usecols=cols)
    g["key"] = [tuple(sorted(p)) for p in zip(g.i_iso3, g.j_iso3)]
    g = g.drop_duplicates("key")
    return dict(zip(g["key"], g.drop(columns=["key"]).to_dict("records")))


def perm_pvalue(labels_a, labels_b, score, rng):
    obs = score(labels_a, labels_b)
    b = np.array(labels_b)
    null = np.array([score(labels_a, rng.permutation(b)) for _ in range(N_PERM)])
    return obs, (1 + (null >= obs).sum()) / (1 + N_PERM)


def main():
    OUT.mkdir(exist_ok=True)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 100)
    rng = np.random.default_rng(SEED)

    iso = load_iso3()
    prof = bg.load_country_profiles("all")
    G, J = bg.build_country_graph(prof)
    countries = list(prof.index)
    part = nx.community.louvain_communities(G, weight="weight", seed=SEED)
    comm = {n: i for i, c in enumerate(sorted(part, key=len, reverse=True)) for n in c}

    un = pd.read_csv(GEO / "un_regions_all.csv", keep_default_na=False).set_index("alpha-3")
    tab = pd.DataFrame({"pays": countries, "iso3": [iso[c] for c in countries]})
    tab["communaute"] = tab["pays"].map(comm)
    # codes ISO3 obsoletes utilises par EnviDat/CEPII -> codes actuels pour la table ONU
    un_code = tab["iso3"].replace({"ZAR": "COD", "ROM": "ROU"})
    tab["region"] = un_code.map(un["region"]).replace("", np.nan)
    tab["sous_region"] = un_code.map(un["sub-region"]).replace("", np.nan)
    miss = tab[tab.region.isna()]
    print(f"Pays sans region ONU (a corriger a la main) : {len(miss)}")
    print(miss[["pays", "iso3"]].to_string(index=False))
    tab.to_csv(OUT / "geo_pays_communautes.csv", index=False, encoding="utf-8-sig")
    t = tab.dropna(subset=["region"]).copy()

    # ---------------- 1. communautes vs regions ONU ----------------
    print("\n== 1. Communautes Louvain vs regions ONU ==")
    print(f"pays comparés : {len(t)} | communautés : {t.communaute.nunique()}")
    for lab in ("region", "sous_region"):
        for name, fn in (("NMI", normalized_mutual_info_score), ("ARI", adjusted_rand_score)):
            obs, p = perm_pvalue(t.communaute.to_numpy(), t[lab].to_numpy(), fn, rng)
            print(f"  {lab:12s} {name} = {obs:.3f}  (p permutation = {p:.4f}, {t[lab].nunique()} classes)")
    ct = pd.crosstab(t.communaute, t.region)
    print("\nTable de contingence communaute x region :\n", ct)
    ct.to_csv(OUT / "geo_contingence.csv", encoding="utf-8-sig")
    ct2 = pd.crosstab(t.communaute, t.sous_region)
    ct2.to_csv(OUT / "geo_contingence_sous_region.csv", encoding="utf-8-sig")

    # pays "atypiques" : region differente de la region majoritaire de leur communaute
    major = t.groupby("communaute")["region"].agg(lambda s: s.value_counts().index[0])
    t["region_majoritaire"] = t.communaute.map(major)
    odd = t[(t.region != t.region_majoritaire)]
    print(f"\nPays hors de la region majoritaire de leur communaute : {len(odd)} / {len(t)}")
    print(odd[["pays", "region", "sous_region", "communaute", "region_majoritaire"]]
          .sort_values(["communaute", "region"]).to_string(index=False))

    # ---------------- 2. similarite vs distance ----------------
    print("\n== 2. Similarite culinaire (Jaccard) vs distance ==")
    pairs = load_pairs()
    idx = {c: i for i, c in enumerate(countries)}
    rows = []
    reg = tab.set_index("pays")["region"]
    sub = tab.set_index("pays")["sous_region"]
    for a in range(len(countries)):
        for b in range(a + 1, len(countries)):
            ca, cb = countries[a], countries[b]
            key = tuple(sorted((iso[ca], iso[cb])))
            if key in pairs:
                p = pairs[key]
                rows.append({"a": ca, "b": cb, "jaccard": J[a, b], "dist": p["dist"],
                             "contig": p["contig"], "comlang": p["comlang_off"],
                             "colony": p["colony"], "comcol": p["comcol"],
                             "lsa": p["food_sim_lsa"], "manhattan": p["food_sim_manhattan"],
                             "same_region": reg.get(ca) == reg.get(cb) and pd.notna(reg.get(ca)),
                             "same_sub": sub.get(ca) == sub.get(cb) and pd.notna(sub.get(ca)),
                             "same_comm": comm[ca] == comm[cb]})
    P = pd.DataFrame(rows)
    print(f"paires avec distance : {len(P)} / {len(countries) * (len(countries) - 1) // 2}")
    P.to_csv(OUT / "geo_paires.csv", index=False, encoding="utf-8-sig")

    rho, pv = spearmanr(P.dist, P.jaccard)
    print(f"Spearman(Jaccard, distance) = {rho:.3f} (p={pv:.2g})")
    far = P[P.dist >= 3000]
    rho_f, pv_f = spearmanr(far.dist, far.jaccard)
    print(f"  seulement paires >= 3000 km ({len(far)}) : {rho_f:.3f} (p={pv_f:.2g})")
    print("Jaccard moyen selon les liens :")
    for col in ("contig", "comlang", "colony", "same_region", "same_sub"):
        m = P.groupby(col)["jaccard"].agg(["mean", "count"]).round(3)
        print(f"  {col}: " + " | ".join(f"{k}: {v['mean']} (n={int(v['count'])})" for k, v in m.iterrows()))

    # OLS : Jaccard ~ log(dist) + contig + comlang + colony + same_region
    X = pd.DataFrame({
        "const": 1.0,
        "log_dist": np.log(P.dist),
        "contig": P.contig.astype(float),
        "comlang": P.comlang.astype(float),
        "colony": P.colony.astype(float),
        "meme_region": P.same_region.astype(float),
    })
    y = P.jaccard.to_numpy()
    beta, *_ = np.linalg.lstsq(X.to_numpy(), y, rcond=None)
    resid = y - X.to_numpy() @ beta
    r2 = 1 - resid.var() / y.var()
    Xs = (X.iloc[:, 1:] - X.iloc[:, 1:].mean()) / X.iloc[:, 1:].std()
    bstd, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(Xs)), Xs.to_numpy()]), (y - y.mean()) / y.std(), rcond=None)
    print(f"\nOLS (R2 = {r2:.3f}) — coefficients bruts / standardises :")
    for n, b, bs in zip(X.columns, beta, np.r_[np.nan, bstd[1:]]):
        print(f"  {n:12s} {b: .4f}   {bs: .3f}")
    print("  (attention : les paires ne sont pas independantes, les p-values classiques seraient trompeuses)")

    # ---------------- 3. connexions inattendues ----------------
    print("\n== 3. Paires culinairement proches mais lointaines (>= 8000 km, hors meme region) ==")
    unexp = P[(P.dist >= 8000) & (~P.same_region)].sort_values("jaccard", ascending=False).head(15)
    print(unexp[["a", "b", "jaccard", "dist", "colony", "comlang"]].round(3).to_string(index=False))

    # ---------------- 4. validation vs auteurs ----------------
    print("\n== 4. Validation : notre Jaccard vs similarites des auteurs ==")
    for c in ("lsa", "manhattan"):
        r, _ = spearmanr(P.jaccard, P[c])
        print(f"  Spearman(Jaccard, {c}) = {r:.3f}")
    prof_n = bg.load_country_profiles("national")
    _, Jn = bg.build_country_graph(prof_n)
    cn = list(prof_n.index)
    jn = {tuple(sorted((a, b))): Jn[i, j] for i, a in enumerate(cn) for j, b in enumerate(cn) if i < j}
    P["jaccard_national"] = [jn.get(tuple(sorted((a, b)))) for a, b in zip(P.a, P.b)]
    r, _ = spearmanr(P.jaccard_national, P.lsa, nan_policy="omit")
    print(f"  Spearman(Jaccard plat national seul, lsa) = {r:.3f}")

    # ---------------- figure ----------------
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    s = P.sample(min(4000, len(P)), random_state=SEED)
    ax[0].scatter(s.dist, s.jaccard, s=4, alpha=.25, color="#7f7f7f")
    bins = pd.qcut(P.dist, 12)
    g = P.groupby(bins, observed=True).agg(d=("dist", "median"), j=("jaccard", "median"))
    ax[0].plot(g.d, g.j, color="#d62728", marker="o", label="médiane par tranche")
    ax[0].set_xscale("log")
    ax[0].set_xlabel("Distance (km, échelle log)")
    ax[0].set_ylabel("Similarité de Jaccard")
    ax[0].set_title(f"Similarité vs distance (Spearman = {rho:.2f})")
    ax[0].legend()

    ct_n = ct.div(ct.sum(axis=1), axis=0)
    im = ax[1].imshow(ct_n.to_numpy(), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax[1].set_xticks(range(ct_n.shape[1]), ct_n.columns, rotation=30)
    ax[1].set_yticks(range(ct_n.shape[0]), [f"C{c} (n={int(ct.loc[c].sum())})" for c in ct_n.index])
    for i in range(ct_n.shape[0]):
        for j in range(ct_n.shape[1]):
            if ct.iloc[i, j]:
                ax[1].text(j, i, int(ct.iloc[i, j]), ha="center", va="center", fontsize=8)
    ax[1].set_title("Communautés Louvain × régions de l'ONU")
    fig.colorbar(im, ax=ax[1], fraction=.046, label="part de la communauté")

    grp = P.groupby(["same_region"]).jaccard.mean()
    ax[2].bar(["régions différentes", "même région"], [grp.get(False, 0), grp.get(True, 0)],
              color=["#1f77b4", "#d62728"])
    ax[2].set_ylabel("Jaccard moyen")
    ax[2].set_title("Similarité moyenne selon la région")
    fig.tight_layout()
    fig.savefig(OUT / "geographie.png", dpi=130)
    print("\nfigure : outputs/geographie.png")


if __name__ == "__main__":
    main()
