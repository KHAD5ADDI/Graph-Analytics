"""Visualisation interactive des deux graphes (pour l'oral et le README).

Sortie : outputs/graphes_interactifs.html, un fichier autonome (donnees et code integres)
a ouvrir dans un navigateur. Seule la police Google Fonts est chargee en ligne ; hors
connexion, la page retombe sur une police systeme.

- Onglet Ingredients : couleur = communaute Louvain, anneau = ingredient pont
  (meme definition que fig_ingredients.png : participation la plus elevee
  parmi les ingredients de degre >= 20).
- Onglet Pays : couleur = communaute Louvain ou region de l'ONU (bascule).
- Survol : mesures du noeud. Clic : voisins les plus forts dans le graphe COMPLET.
- Comme pour les figures statiques, seules les aretes les plus fortes de chaque
  noeud sont dessinees (squelette) ; les mesures viennent du graphe complet
  (outputs/*_nodes.csv, produits par analyze.py).

Pre-requis : build_graphs.py, analyze.py et geography.py deja executes.
Usage : python src/interactive.py
"""
import json
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
PROC = ROOT / "data" / "processed"
TEMPLATE = Path(__file__).resolve().parent / "interactive_template.html"
SEED = 42
N_NEIGHBOURS = 8


def backbone(G, k):
    """Union des k aretes les plus fortes de chaque noeud (affichage seulement)."""
    keep = set()
    for n in G:
        nb = sorted(G[n].items(), key=lambda x: x[1]["weight"], reverse=True)[:k]
        keep.update(tuple(sorted((n, m))) for m, _ in nb)
    B = nx.Graph()
    B.add_nodes_from(G.nodes())
    B.add_edges_from((u, v, {"weight": G[u][v]["weight"]}) for u, v in keep)
    return B


def normalise(pos):
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = max(x1 - x0, y1 - y0) or 1
    return {n: ((p[0] - x0) / s, (p[1] - y0) / s) for n, p in pos.items()}


def relabel_by_size(comm):
    """Communautes renumerotees par taille decroissante (0 = la plus grande)."""
    sizes = pd.Series(comm).value_counts()
    order = {c: i for i, c in enumerate(sizes.index)}
    return {n: order[c] for n, c in comm.items()}


def node_records(G, measures, comm, pos, extra=None):
    recs = []
    for n in G:
        m = measures.loc[n]
        nb = sorted(G[n].items(), key=lambda x: x[1]["weight"], reverse=True)[:N_NEIGHBOURS]
        r = {
            "id": n, "x": round(pos[n][0], 4), "y": round(pos[n][1], 4), "c": int(comm[n]),
            "deg": int(m["degre"]), "force": round(float(m["force"]), 2),
            "btw": round(float(m["intermediarite"]), 4),
            # vecteur propre defini sur la plus grande composante seulement : null ailleurs
            "eig": None if pd.isna(m["vecteur_propre"]) else round(float(m["vecteur_propre"]), 4),
            "part": round(float(m["participation"]), 3),
            "nb": [[v, round(float(d["weight"]), 3)] for v, d in nb],
        }
        if extra:
            r.update(extra(n))
        recs.append(r)
    return recs


def communities_summary(recs, n_top=3):
    out = []
    for c in sorted({r["c"] for r in recs}):
        members = sorted((r for r in recs if r["c"] == c), key=lambda r: -r["force"])
        out.append({"id": c, "size": len(members), "top": [r["id"] for r in members[:n_top]]})
    return out


def ingredients():
    G = nx.read_graphml(PROC / "ingredient_graph.graphml")
    meas = pd.read_csv(OUT / "ingredients_nodes.csv", index_col=0, encoding="utf-8-sig")
    comm = relabel_by_size(meas["communaute"].to_dict())
    B = backbone(G, 6)
    pos = normalise(nx.spring_layout(B, weight="weight", k=0.35, iterations=300, seed=SEED))
    cats = nx.get_node_attributes(G, "category")
    nrec = nx.get_node_attributes(G, "n_recipes")
    recs = node_records(G, meas, comm, pos,
                        lambda n: {"cat": cats.get(n, ""), "nrec": int(nrec.get(n, 0))})
    bridges = sorted((r for r in recs if r["deg"] >= 20), key=lambda r: -r["part"])[:12]
    for r in recs:
        r["bridge"] = r["id"] in {b["id"] for b in bridges}
    return {
        "key": "ingredients", "nodes": recs,
        "edges": [[u, v, round(float(d["weight"]), 3)] for u, v, d in B.edges(data=True)],
        "communities": communities_summary(recs),
        "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(), "n_shown": B.number_of_edges(),
        "weight_label": "PMI", "source": "CulinaryDB (CoSyLab, IIIT-Delhi)",
    }


def countries():
    G = nx.read_graphml(PROC / "country_graph.graphml")
    meas = pd.read_csv(OUT / "countries_nodes.csv", index_col=0, encoding="utf-8-sig")
    geo = pd.read_csv(OUT / "geo_pays_communautes.csv", encoding="utf-8-sig").set_index("pays")
    comm = relabel_by_size(geo["communaute"].to_dict())
    B = backbone(G, 5)
    comps = sorted(nx.connected_components(B), key=len, reverse=True)
    pos = nx.spring_layout(B.subgraph(comps[0]), weight="weight", k=0.22, iterations=500, seed=SEED)
    pos = normalise(pos)
    rest = [n for c in comps[1:] for n in sorted(c)]
    for i, n in enumerate(rest):   # pays hors de la plus grande composante : une ligne en bas
        pos[n] = ((i + 0.5) / len(rest), 1.12)
    ning = nx.get_node_attributes(G, "n_ingredients")
    recs = node_records(G, meas, comm, pos, lambda n: {
        "region": geo.loc[n, "region"], "sub": geo.loc[n, "sous_region"],
        "ning": int(ning.get(n, 0)), "lcc": n not in rest})
    return {
        "key": "pays", "nodes": recs,
        "edges": [[u, v, round(float(d["weight"]), 3)] for u, v, d in B.edges(data=True)],
        "communities": communities_summary(recs),
        "n_nodes": G.number_of_nodes(), "n_edges": G.number_of_edges(), "n_shown": B.number_of_edges(),
        "weight_label": "Jaccard", "source": "Wunderlich & Kohler (2022), EnviDat",
    }


if __name__ == "__main__":
    data = {"ingredients": ingredients(), "pays": countries()}
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    page = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            "</head>\n<body>\n" + html + "\n</body>\n</html>\n")
    (OUT / "graphes_interactifs.html").write_text(page, encoding="utf-8")
    print("outputs/graphes_interactifs.html :",
          {k: (len(v["nodes"]), len(v["edges"])) for k, v in data.items()})
