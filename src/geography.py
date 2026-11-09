"""Culinary proximity vs geography (objective 3 of the project).

Sources to cite:
- Wunderlich & Kohler (2022), EnviDat, doi:10.16904/envidat.276 (ODbL):
  national dishes plus gravity variables (distance, borders, language, colonial ties)
- UN M49 regions: repository lukes/ISO-3166-Countries-with-Regional-Codes (GitHub)

Analyses:
  1. Do the Louvain communities overlap the UN regions? (contingency table, NMI / ARI,
     permutation test). Communities are numbered by decreasing size, as everywhere else.
  2. Does culinary similarity (Jaccard) decrease with distance? (Spearman, OLS)
  3. Unexpected connections: close in cuisine but far apart, and countries whose
     community does not match their region.
  4. Validation against the authors' similarity measures (Manhattan, LSA).

NMI / ARI / OLS are kept in the repository only; the report uses the contingency table
and B's shuffle test (src/shuffle_test.py).

Usage: python src/geography.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
    part = an.louvain_partition(G)
    comm = an.community_map(part)

    un = pd.read_csv(GEO / "un_regions_all.csv", keep_default_na=False).set_index("alpha-3")
    tab = pd.DataFrame({"country": countries, "iso3": [iso[c] for c in countries]})
    tab["community"] = tab["country"].map(comm)
    # obsolete ISO3 codes used by EnviDat / CEPII -> current codes for the UN table
    un_code = tab["iso3"].replace({"ZAR": "COD", "ROM": "ROU"})
    tab["region"] = un_code.map(un["region"]).replace("", np.nan)
    tab["subregion"] = un_code.map(un["sub-region"]).replace("", np.nan)
    miss = tab[tab.region.isna()]
    print(f"Countries without a UN region: {len(miss)}")
    if len(miss):
        print(miss[["country", "iso3"]].to_string(index=False))
    tab.to_csv(OUT / "geo_pays_communautes.csv", index=False, encoding="utf-8-sig")
    t = tab.dropna(subset=["region"]).copy()

    # ---------------- 1. communities vs UN regions ----------------
    print("\n== 1. Louvain communities vs UN regions ==")
    print(f"countries compared: {len(t)} | communities: {t.community.nunique()}")
    for lab in ("region", "subregion"):
        for name, fn in (("NMI", normalized_mutual_info_score), ("ARI", adjusted_rand_score)):
            obs, p = perm_pvalue(t.community.to_numpy(), t[lab].to_numpy(), fn, rng)
            print(f"  {lab:10s} {name} = {obs:.3f}  (permutation p = {p:.4f}, {t[lab].nunique()} classes)")
    ct = pd.crosstab(t.community, t.region)
    print("\nContingency table, community x region:\n", ct)
    ct.to_csv(OUT / "geo_contingence.csv", encoding="utf-8-sig")
    pd.crosstab(t.community, t.subregion).to_csv(OUT / "geo_contingence_sous_region.csv", encoding="utf-8-sig")

    # countries outside the majority region of their community
    major = t.groupby("community")["region"].agg(lambda s: s.value_counts().index[0])
    t["majority_region"] = t.community.map(major)
    odd = t[t.region != t.majority_region]
    print(f"\nCountries outside the majority region of their community: {len(odd)} / {len(t)}")
    print(odd[["country", "region", "subregion", "community", "majority_region"]]
          .sort_values(["community", "region"]).to_string(index=False))

    # ---------------- 2. similarity vs distance ----------------
    print("\n== 2. Culinary similarity (Jaccard) vs distance ==")
    pairs = load_pairs()
    rows = []
    reg = tab.set_index("country")["region"]
    sub = tab.set_index("country")["subregion"]
    for a in range(len(countries)):
        for b in range(a + 1, len(countries)):
            ca, cb = countries[a], countries[b]
            key = tuple(sorted((iso[ca], iso[cb])))
            if key in pairs:
                p = pairs[key]
                rows.append({"country_a": ca, "country_b": cb, "jaccard": J[a, b],
                             "distance_km": p["dist"], "contiguous": p["contig"],
                             "common_language": p["comlang_off"], "colony": p["colony"],
                             "common_colonizer": p["comcol"],
                             "authors_lsa": p["food_sim_lsa"], "authors_manhattan": p["food_sim_manhattan"],
                             "same_region": reg.get(ca) == reg.get(cb) and pd.notna(reg.get(ca)),
                             "same_subregion": sub.get(ca) == sub.get(cb) and pd.notna(sub.get(ca)),
                             "same_community": comm[ca] == comm[cb]})
    P = pd.DataFrame(rows)
    print(f"pairs with a distance: {len(P)} / {len(countries) * (len(countries) - 1) // 2}")
    P.to_csv(OUT / "geo_paires.csv", index=False, encoding="utf-8-sig")

    rho, pv = spearmanr(P.distance_km, P.jaccard)
    print(f"Spearman(Jaccard, distance) = {rho:.3f} (p={pv:.2g})")
    far = P[P.distance_km >= 3000]
    rho_f, pv_f = spearmanr(far.distance_km, far.jaccard)
    print(f"  pairs >= 3000 km only ({len(far)}): {rho_f:.3f} (p={pv_f:.2g})")
    print("Mean Jaccard by relation:")
    for col in ("contiguous", "common_language", "colony", "same_region", "same_subregion"):
        m = P.groupby(col)["jaccard"].agg(["mean", "count"]).round(3)
        print(f"  {col}: " + " | ".join(f"{k}: {v['mean']} (n={int(v['count'])})" for k, v in m.iterrows()))

    # OLS: Jaccard ~ log(distance) + contiguous + common language + colony + same region
    X = pd.DataFrame({
        "const": 1.0,
        "log_distance": np.log(P.distance_km),
        "contiguous": P.contiguous.astype(float),
        "common_language": P.common_language.astype(float),
        "colony": P.colony.astype(float),
        "same_region": P.same_region.astype(float),
    })
    y = P.jaccard.to_numpy()
    beta, *_ = np.linalg.lstsq(X.to_numpy(), y, rcond=None)
    resid = y - X.to_numpy() @ beta
    r2 = 1 - resid.var() / y.var()
    Xs = (X.iloc[:, 1:] - X.iloc[:, 1:].mean()) / X.iloc[:, 1:].std()
    bstd, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(Xs)), Xs.to_numpy()]), (y - y.mean()) / y.std(), rcond=None)
    print(f"\nOLS (R2 = {r2:.3f}), raw / standardised coefficients:")
    for n, b, bs in zip(X.columns, beta, np.r_[np.nan, bstd[1:]]):
        print(f"  {n:16s} {b: .4f}   {bs: .3f}")
    print("  (country pairs are not independent: classical p-values would be misleading)")

    # ---------------- 3. unexpected connections ----------------
    print("\n== 3. Close in cuisine but far apart (>= 8000 km, different regions) ==")
    unexp = P[(P.distance_km >= 8000) & (~P.same_region)].sort_values("jaccard", ascending=False).head(15)
    print(unexp[["country_a", "country_b", "jaccard", "distance_km", "colony", "common_language"]]
          .round(3).to_string(index=False))

    # ---------------- 4. validation against the authors ----------------
    print("\n== 4. Validation: our Jaccard vs the authors' similarity measures ==")
    for c in ("authors_lsa", "authors_manhattan"):
        r, _ = spearmanr(P.jaccard, P[c])
        print(f"  Spearman(Jaccard, {c}) = {r:.3f}")
    prof_n = bg.load_country_profiles("national")
    _, Jn = bg.build_country_graph(prof_n)
    cn = list(prof_n.index)
    jn = {tuple(sorted((a, b))): Jn[i, j] for i, a in enumerate(cn) for j, b in enumerate(cn) if i < j}
    P["jaccard_national"] = [jn.get(tuple(sorted((a, b)))) for a, b in zip(P.country_a, P.country_b)]
    r, _ = spearmanr(P.jaccard_national, P.authors_lsa, nan_policy="omit")
    print(f"  Spearman(Jaccard of the national dish only, authors_lsa) = {r:.3f}"
          " (circular: same dish data as the authors)")

    # ---------------- figure ----------------
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    s = P.sample(min(4000, len(P)), random_state=SEED)
    ax[0].scatter(s.distance_km, s.jaccard, s=4, alpha=.25, color="#7f7f7f")
    bins = pd.qcut(P.distance_km, 12)
    g = P.groupby(bins, observed=True).agg(d=("distance_km", "median"), j=("jaccard", "median"))
    ax[0].plot(g.d, g.j, color="#d62728", marker="o", label="median per bin")
    ax[0].set_xscale("log")
    ax[0].set_xlabel("Distance (km, log scale)")
    ax[0].set_ylabel("Jaccard similarity")
    ax[0].set_title(f"Similarity vs distance (Spearman = {rho:.2f})")
    ax[0].legend()

    ct_n = ct.div(ct.sum(axis=1), axis=0)
    im = ax[1].imshow(ct_n.to_numpy(), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax[1].set_xticks(range(ct_n.shape[1]), ct_n.columns, rotation=30)
    ax[1].set_yticks(range(ct_n.shape[0]), [f"C{c} (n={int(ct.loc[c].sum())})" for c in ct_n.index])
    for i in range(ct_n.shape[0]):
        for j in range(ct_n.shape[1]):
            if ct.iloc[i, j]:
                ax[1].text(j, i, int(ct.iloc[i, j]), ha="center", va="center", fontsize=8)
    ax[1].set_title("Louvain communities x UN regions")
    fig.colorbar(im, ax=ax[1], fraction=.046, label="share of the community")

    grp = P.groupby(["same_region"]).jaccard.mean()
    ax[2].bar(["different regions", "same region"], [grp.get(False, 0), grp.get(True, 0)],
              color=["#1f77b4", "#d62728"])
    ax[2].set_ylabel("Mean Jaccard")
    ax[2].set_title("Mean similarity by region")
    fig.tight_layout()
    fig.savefig(OUT / "geographie.png", dpi=130)
    print("\nfigure: outputs/geographie.png")


if __name__ == "__main__":
    main()
