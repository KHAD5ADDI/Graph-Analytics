<div align="center">

# The Hidden Bridges of World Cuisines

### _Graph analysis of ingredient combinations and of the links between national cuisines_

<p><em>Finding the ingredients that connect culinary traditions, and testing whether culinary proximity follows geography.</em></p>

![Status](https://img.shields.io/badge/status-analysis_complete-success?style=flat)
![Version](https://img.shields.io/badge/version-1.0-blue?style=flat)
![Data license](https://img.shields.io/badge/data-CC_BY--NC--SA_%2B_ODbL-brightgreen?style=flat)
![Course](https://img.shields.io/badge/Albert_School-Graph_Analytics-red?style=flat)

<p><em>Built with:</em></p>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat)
![NetworkX](https://img.shields.io/badge/NetworkX-3.7-orange?style=flat)
![pandas](https://img.shields.io/badge/pandas-3.0.2-150458?style=flat)
![NumPy](https://img.shields.io/badge/NumPy-2.4.4-013243?style=flat)
![SciPy](https://img.shields.io/badge/SciPy-1.17.1-8CAAE6?style=flat)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8.0-F7931E?style=flat)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.10.0-11557C?style=flat)

Group project, Graph Analytics course, Albert School, 2026

**[Results](#results) · [Architecture](#technical-architecture) · [Limitations](#limitations-and-residual-risks)**

</div>

> [!TIP]
> **Reproduce the whole analysis**
>
> 1. Install the dependencies: `pip install -r requirements.txt`
> 2. Move to the source folder: `cd src`
> 3. Run the pipeline in this order:
>
>    ```bash
>    python build_graphs.py   # cleaning + both graphs -> data/processed/
>    python analyze.py        # measures, Louvain, sensitivity (about 2 min)
>    python robustness.py     # removal experiments on the ingredient graph
>    python geography.py      # communities vs UN regions, similarity vs distance
>    python visualize.py      # network figures (needs the output of geography.py)
>    ```
>
> 4. Tables (CSV) and figures (PNG) are written to `outputs/`. All thresholds are parameters at the top of `src/build_graphs.py`.

---

## Table of contents

- [Project goal](#project-goal)
- [Features](#features)
  - [1. Data and cleaning](#1-data-and-cleaning)
  - [2. The ingredient graph](#2-the-ingredient-graph)
  - [3. The country graph](#3-the-country-graph)
  - [4. Measures required by the brief](#4-measures-required-by-the-brief)
  - [5. Bridge ingredients and robustness](#5-bridge-ingredients-and-robustness)
  - [6. Culinary proximity vs geography](#6-culinary-proximity-vs-geography)
  - [7. Visualisations](#7-visualisations)
- [Results](#results)
- [Limitations and residual risks](#limitations-and-residual-risks)
- [Technical architecture](#technical-architecture)
- [Project structure](#project-structure)
- [Installation and setup](#installation-and-setup)
- [Data sources and versions](#data-sources-and-versions)
- [Technical decisions](#technical-decisions)
- [Use of AI](#use-of-ai)
- [Team](#team)

---

## Project goal

Which ingredients act as bridges between culinary traditions, and does a graph analysis reveal links that simple frequency comparisons miss?

Three objectives:

1. Identify families of ingredients that are used together.
2. Find the "bridge" ingredients between distinct culinary communities.
3. Test whether culinary proximity between countries follows geography or reveals unexpected connections.

No data was collected by the team: every source is public, open, and cited. Most existing studies of ingredient networks rely on about twenty cuisines; this project adds a second, country-level graph covering 171 countries, and tests the findings against geography.

## Features

### 1. Data and cleaning

| Source | Content | Licence | Folder |
| --- | --- | --- | --- |
| [CulinaryDB](https://cosylab.iiitd.edu.in/culinarydb/) (CoSyLab, IIIT-Delhi) | 45,772 recipes, 26 cuisine labels, 695 distinct ingredients used, 456,279 recipe-ingredient pairs | CC BY-NC-SA 3.0 | `data/raw/culinarydb/` |
| National dishes of 171 countries, Wunderlich & Kohler (2022), [EnviDat](https://doi.org/10.16904/envidat.276), file `foodculture_dishes_rev2.csv` | 351 dishes (171 national dishes + 180 other dishes), 218 ingredient columns | ODbL + DbCL | `data/raw/envidat/` |
| Same EnviDat dataset, file `gravity_food_sim_final.csv` | distance, contiguity, common language, colonial ties, the authors' food-similarity measures | ODbL + DbCL | `data/raw/geography/` |
| UN M49 regions per ISO3 code ([lukes/ISO-3166-Countries-with-Regional-Codes](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes)) | region and sub-region of each country | see repository | `data/raw/geography/` |

Cleaning applied in [build_graphs.py](src/build_graphs.py) and [geography.py](src/geography.py):

- **CulinaryDB:** duplicate recipe-ingredient pairs are removed (456,279 to 412,560 pairs). The 103 compound ingredients (e.g. Garam Masala) are kept as nodes with a `compound` attribute.
- **EnviDat:** the CSV is `cp1252`-encoded with `;` separators; one empty row and one stray value (`58` in `coriander_cilantro`) are discarded.
- **Country codes:** EnviDat and CEPII use two obsolete ISO3 codes (`ZAR` to `COD`, `ROM` to `ROU`), mapped when joining with the UN regions. Joins use ISO3 codes, never country names. Typos present in the original data (e.g. "Roumania") are left untouched.

RecipeDB (IIIT-Delhi, about 118,000 recipes) was considered first. It has no bulk download and no public repository, so CulinaryDB, from the same lab, was used instead.

### 2. The ingredient graph

| | |
| --- | --- |
| Nodes | ingredients present in at least 50 recipes (362) |
| Edges | co-occurrence in at least 10 recipes **and** PMI > 0 |
| Weight | PMI: log2( c_ij · N / (c_i · c_j) ), association beyond chance |
| Type | undirected, simple, weighted |

### 3. The country graph

| | |
| --- | --- |
| Nodes | the 171 countries |
| Country profile | union of the ingredients of **all** the country's dishes (alternative tested: national dish only) |
| Edges | Jaccard similarity of ingredient sets of at least 0.30 |
| Weight | Jaccard similarity |
| Type | undirected, simple, weighted |

### 4. Measures required by the brief

[analyze.py](src/analyze.py) computes, for each graph: number of nodes and edges, density, connected components, diameter and radius, clustering, degree / weighted degree, betweenness, eigenvector centrality, Louvain communities and modularity, and a sensitivity analysis to the thresholds.

Conventions:

- diameter and radius are computed on the **largest connected component** of the **unweighted** graph (number of hops);
- betweenness uses distance = 1 / weight (a strong weight means proximity);
- eigenvector centrality is defined on the largest connected component only;
- Louvain runs on the weighted graph with `seed=42`.

### 5. Bridge ingredients and robustness

A bridge ingredient is defined with the **participation coefficient** (Guimera & Amaral): P_i = 1 − Σ_c (k_ic / k_i)², computed on the Louvain partition, among ingredients of degree at least 20 (to avoid low-degree artefacts).

[robustness.py](src/robustness.py) removes k ingredients (k from 0 to 60 out of 362) following five strategies (participation, betweenness, frequency, degree, random with 20 draws) and measures the global efficiency, the share of nodes in the largest component, the weight of inter-community edges (original partition), and the modularity recomputed with Louvain. The experiment is repeated on a sparser graph (PMI ≥ 0.5, at least 20 recipes) to check that conclusions hold.

### 6. Culinary proximity vs geography

[geography.py](src/geography.py) compares the country graph with UN regions and with distance:

- agreement between Louvain communities and UN regions / sub-regions (NMI and ARI, with a 2,000-draw permutation test);
- Spearman correlation between Jaccard similarity and distance, and an OLS regression with log-distance, contiguity, common language, colonial tie, and same region;
- list of culinarily close but distant country pairs, and of countries outside the dominant region of their community;
- validation against the similarity measures of the EnviDat authors (Manhattan and LSA).

### 7. Visualisations

[visualize.py](src/visualize.py) draws the strongest edges of each node (a backbone) for readability; all measures are computed on the full graphs. Node positions come from a force-directed layout and carry no geographic meaning.

## Results

### Global measures

| Measure | Ingredients | Countries (Jaccard ≥ 0.30) |
| --- | ---: | ---: |
| Nodes | 362 | 171 |
| Edges | 10,853 | 2,066 |
| Density | 0.166 | 0.142 |
| Connected components | 1 | 5 |
| Largest component | 362 | 166 |
| Diameter / radius (largest component) | 3 / 2 | 6 / 3 |
| Average clustering | 0.591 | 0.478 |
| Louvain communities | 5 | 11 |
| Modularity | 0.400 | 0.286 |

Source: [analyze.py](src/analyze.py); tables in `outputs/ingredients_nodes.csv` and `outputs/countries_nodes.csv`.

### Ingredient communities

![Ingredient graph](outputs/fig_ingredients.png)

| Community | Size | Strongest ingredients |
| --- | ---: | --- |
| 0 | 112 | shallot, bay laurel, carrot, celery, thyme, fennel, parsley, mushroom |
| 1 | 97 | cinnamon, vanilla, coconut, orange, nutmeg, raisin, sugar, honey |
| 2 | 57 | lettuce, mustard, beans, mayonnaise, onion, beef, pork |
| 3 | 55 | ginger, welsh onion, shrimp, fish, soy sauce, lime, sesame, coconut milk |
| 4 | 41 | coriander, turmeric, clove, cumin, chickpea, cayenne, peas |

Bridge ingredients (highest participation coefficient, degree ≥ 20): okra, cooking oil, Mexican oregano, coriander seed, cumin, coriander, liquid smoke, lime, corn oil, cayenne. By betweenness: couscous, lasagna, shallot, coconut, saffron.

**Bridges are not the most frequent ingredients:** the overlap of the top 20 with the top 20 by frequency (salt, pepper, garlic, onion, olive…) is 0.08 (Jaccard) for participation and 0.00 for betweenness.

### Sensitivity to the thresholds

Ingredient graph (selection from [sensibilite_ingredients.csv](outputs/sensibilite_ingredients.csv)):

| Min. co-occurrence | PMI threshold | Edges | Components | Louvain communities | Modularity |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 (**chosen**) | 0.0 | 10,853 | 1 | 5 | 0.400 |
| 10 | 0.5 | 7,745 | 1 | 5 | 0.423 |
| 10 | 1.0 | 4,910 | 2 | 7 | 0.477 |
| 20 | 0.0 | 7,873 | 3 | 8 | 0.414 |
| 50 | 0.0 | 4,522 | 40 | 44 | 0.441 |

Country graph, all-dishes profile ([sensibilite_pays.csv](outputs/sensibilite_pays.csv)):

| Jaccard threshold | Edges | Components | Largest component | Louvain communities | Modularity |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 7,447 | 1 | 171 | 4 | 0.123 |
| 0.25 | 4,466 | 3 | 169 | 7 | 0.183 |
| **0.30 (chosen)** | 2,066 | 5 | 166 | 11 | 0.286 |
| 0.35 | 835 | 17 | 153 | 23 | 0.437 |
| 0.40 | 331 | 36 | 130 | 41 | 0.600 |

Modularity rises with stricter thresholds only because the graph breaks into small pieces; the chosen values are the best trade-off between structure and connectivity.

### Robustness of the ingredient graph (k = 60 ingredients removed)

![Robustness](outputs/robustesse_defaut.png)

| Strategy | Global efficiency | Largest component | Inter-community edge weight | Modularity |
| --- | ---: | ---: | ---: | ---: |
| none (reference) | 0.580 | 1.000 | 0.376 | 0.400 |
| random (mean of 20) | 0.577 | 1.000 | 0.377 | 0.397 |
| participation (bridges) | 0.563 | 1.000 | 0.283 | 0.441 |
| betweenness | 0.570 | 1.000 | 0.355 | 0.413 |
| frequency | 0.437 | 0.954 | 0.329 | 0.463 |
| degree | 0.442 | 0.964 | 0.284 | 0.503 |

Same experiment on the sparser graph (PMI ≥ 0.5, at least 20 recipes), reference values 0.488 / 0.983 / 0.348 / 0.441: participation 0.441 / 0.974 / 0.212 / 0.530, frequency 0.262 / 0.801 / 0.291 / 0.523, degree 0.295 / 0.864 / 0.250 / 0.562, random 0.478 / 0.979 / 0.348 / 0.440.

### Culinary proximity vs geography

![Geography](outputs/geographie.png)

| Comparison | NMI | ARI | Permutation p |
| --- | ---: | ---: | ---: |
| Louvain communities vs UN regions (5 classes) | 0.352 | 0.251 | < 0.001 |
| Louvain communities vs UN sub-regions (17 classes) | 0.433 | 0.179 | < 0.001 |

| Relation (14,535 country pairs) | Value |
| --- | ---: |
| Spearman(Jaccard, distance) | −0.256 |
| Spearman restricted to pairs ≥ 3,000 km | −0.156 |
| OLS R² (log-distance, contiguity, language, colony, same region) | 0.087 |
| Mean Jaccard, same region / different regions | 0.239 / 0.190 |
| Spearman(Jaccard, authors' LSA similarity) | 0.585 |
| Spearman(Jaccard of the national dish only, authors' LSA) | 0.971 |

Communities by region ([geo_contingence.csv](outputs/geo_contingence.csv)):

| Community (size) | Africa | Americas | Asia | Europe | Oceania |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 (49) | 4 | 9 | 3 | 31 | 2 |
| 1 (42) | 24 | 11 | 4 | 3 | 0 |
| 2 (32) | 8 | 1 | 21 | 2 | 0 |
| 3 (25) | 5 | 13 | 5 | 0 | 2 |
| 4 (9) | 0 | 0 | 9 | 0 | 0 |
| 5 (6) | 1 | 0 | 0 | 0 | 5 |

![Country graph](outputs/fig_pays.png)

### Key findings

- **Ingredient communities are culinarily meaningful:** French herb base, sweet and baking, North-American, East and South-East Asian, and spices.
- **Bridges are structurally distinct from frequent ingredients** (top-20 overlap 0.08), which supports the use of a graph measure rather than counts.
- **Removing bridges does not fragment the graph** (the largest component stays complete), but it removes the links between communities faster than random or frequency-based removal: inter-community weight falls from 0.348 to 0.212 on the sparser graph, against 0.348 (random) and 0.291 (frequency). Removing frequent or high-degree ingredients damages global efficiency far more (0.437 against 0.563). The hypothesis "bridges hold the graph together" is therefore only partly supported: the very common ingredients do that.
- **Culinary proximity follows geography moderately:** East Asia (9 of 9 countries in Asia) and the Pacific (5 of 6 in Oceania) form clear blocks; Europe is a core (31 of 49 countries) mixed with the Americas, Australia, and New Zealand. 61 of 171 countries sit outside the dominant region of their community.
- **Distance explains little** (R² = 0.09). Contiguity, shared language, and colonial ties add almost nothing once distance is accounted for.
- **Unexpected connections** include France, Ireland and Greece with New Zealand or Australia (Jaccard 0.46 to 0.50 at more than 15,000 km), consistent with European culinary heritage in Oceania.
- **Validation:** the country similarity correlates with the authors' own measure (0.585 with all dishes, 0.971 with the national dish only).

## Limitations and residual risks

- **Small country profiles:** median 16 ingredients, 20 countries with 8 or fewer. This inflates Jaccard for some pairs (Palau and Seychelles have 7 ingredients each and a Jaccard of 1.000), and the "bridge" role of small countries (Tonga, Tuvalu) is likely an artefact.
- **Imbalanced CulinaryDB:** USA 16,118 recipes and Italy 7,504, against 15 and 14 for the smallest "Misc." groups. PMI and Louvain results reflect Western cuisines more than the others.
- **Partly circular bridge metric:** bridges are defined with the Louvain partition, and the "inter-community edge weight" uses the same partition. The recomputed modularity is the independent check, and degree-based removal increases it even more than bridge removal on the default graph.
- **Dependent observations:** country pairs are not independent, so the classical p-values of the regression are not reported; only the permutation tests are.
- **Snapshot data:** EnviDat data were collected from 4 June to 23 August 2018.
- **Not a causal claim:** a shared ingredient list does not prove a historical or cultural link.
- **Reuse of prior work:** other university projects have applied Louvain to CulinaryDB. No code from them was used; the originality lies in the bridge definition, the robustness test, and the country-level comparison with geography.

## Technical architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ CulinaryDB (45,772 recipes)      EnviDat (171 countries)      │
└───────────────┬──────────────────────────┬───────────────────┘
                ↓                          ↓
     Cleaning, recipe sets       Country profiles (all dishes)
                ↓                          ↓
   Co-occurrence matrix -> PMI      Jaccard similarity matrix
   (>= 10 recipes, PMI > 0)         (threshold 0.30)
                ↓                          ↓
        Ingredient graph             Country graph
        (362 nodes, 10,853 edges)    (171 nodes, 2,066 edges)
                └────────────┬─────────────┘
                             ↓
        Measures, centralities, Louvain, sensitivity
                             ↓
     ┌───────────────────────┴───────────────────────┐
     ↓                                               ↓
Participation coefficient (bridges)     UN regions + distance (EnviDat)
Removal experiments (robustness)        NMI / ARI, Spearman, OLS
     └───────────────────────┬───────────────────────┘
                             ↓
                 outputs/ (CSV tables and figures)
```

## Project structure

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── culinarydb/               # 4 CSV files (+ original zip)
│   │   ├── envidat/                  # foodculture_dishes_rev2.csv
│   │   └── geography/                # gravity_food_sim_final.csv, un_regions_all.csv
│   └── processed/                    # ingredient_graph.graphml, country_graph.graphml
├── src/
│   ├── build_graphs.py               # cleaning and construction of both graphs (parameters at the top)
│   ├── analyze.py                    # required measures, Louvain, participation, sensitivity
│   ├── robustness.py                 # removal experiments on the ingredient graph
│   ├── geography.py                  # communities vs UN regions, similarity vs distance, validation
│   └── visualize.py                  # network figures
└── outputs/
    ├── ingredients_nodes.csv         # node table (centralities, community, participation)
    ├── countries_nodes.csv
    ├── sensibilite_ingredients.csv   # sensitivity to the thresholds
    ├── sensibilite_pays.csv
    ├── robustesse_*.csv / .png       # removal experiments
    ├── geo_*.csv, geographie.png     # geography analysis
    └── fig_ingredients.png, fig_pays.png
```

## Installation and setup

Prerequisites: Python 3.12 (the version used for all results) and `pip`. No GPU or API key is needed.

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Check that the raw data are in `data/raw/` (they are versioned in this repository). If not, download them from the links in [Data sources and versions](#data-sources-and-versions).

3. Run the pipeline from the `src/` folder:

   ```bash
   cd src
   python build_graphs.py
   python analyze.py
   python robustness.py
   python geography.py
   python visualize.py
   ```

   `analyze.py` takes about 2 minutes (the sensitivity analysis rebuilds the graph for each threshold). On Windows, set `PYTHONIOENCODING=utf-8` if the console fails on accented country names.

## Data sources and versions

| Source | Reference |
| --- | --- |
| CulinaryDB | CoSyLab, IIIT-Delhi. https://cosylab.iiitd.edu.in/culinarydb/ (CC BY-NC-SA 3.0) |
| National dishes, food similarity, gravity variables | Wunderlich, A. & Kohler, A. (2022). *Data of national dishes, their similarity and trade flows.* EnviDat. doi:10.16904/envidat.276 (ODbL + DbCL) |
| UN regions | lukes/ISO-3166-Countries-with-Regional-Codes, `all/all.csv` |

Python libraries (versions used): networkx 3.7, pandas 3.0.2, numpy 2.4.4, scipy 1.17.1, matplotlib 3.10.0, scikit-learn 1.8.0. Data in `data/raw/` keeps its original licence (attribution, non-commercial where stated, share-alike).

## Technical decisions

### Why CulinaryDB rather than RecipeDB or web scraping?

RecipeDB covers more recipes but offers no bulk download or public repository. Scraping recipe sites raises copyright and terms-of-use issues and would have consumed a large share of the ten available days. CulinaryDB is open, citable, and comes from the same lab.

### Why PMI as the ingredient edge weight?

Raw co-occurrence counts are dominated by ubiquitous ingredients (salt, pepper, garlic). PMI measures association beyond chance, and a minimum number of shared recipes (10) limits the well-known instability of PMI for rare pairs.

### Why Jaccard similarity for countries, with a 0.30 threshold?

Jaccard compares ingredient sets without counts, which suits binary dish data. At 0.20 or below, the graph is dense (density above 0.5) and modularity is only 0.12; from 0.35 upward, it breaks into 17 or more components. 0.30 keeps 166 of 171 countries in one component with a clear community structure.

### Why use all dishes of a country instead of the national dish only?

The national dish alone gives about ten ingredients per country, which makes Jaccard very noisy. Both variants were built and compared: the all-dishes profile produces a better-connected graph, while the national-dish profile correlates at 0.971 with the authors' own similarity.

### Why the participation coefficient to define a bridge?

Betweenness favours nodes that lie on shortest paths regardless of communities, whereas the participation coefficient measures directly how evenly an ingredient's links are spread across communities. Both were computed and compared with frequency.

### Why Louvain, with a fixed seed?

Louvain handles weighted graphs and is available in NetworkX. The partition is not unique, so `seed=42` makes it reproducible, and the sensitivity analysis shows how the community count changes with the thresholds.

### Why draw only a backbone in the figures?

With 10,853 edges the full graph is an unreadable blob. The figures keep the strongest edges of each node (6 per node for ingredients, 5 for countries) for the layout and the drawing, while all measures use the complete graphs.

## Use of AI

An AI assistant (Claude, Anthropic) was used to help choose the data sources, write the analysis code and figures, and draft this README. The team reviewed the design choices, thresholds, and interpretations. *[Complete or adjust this paragraph to match the course's declaration template.]* No code from other projects was copied.

## Team

- **Khadidja Addi**: *[role to complete]*
- **[Teammate's name]**: *[role to complete]*

---

**Version 1.0** · Graph Analytics project, Albert School, 2026
