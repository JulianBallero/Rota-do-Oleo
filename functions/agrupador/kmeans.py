"""Agrupamento geográfico de clientes com seleção opcional de K por silhouette."""
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

PALETTE = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46f0f0",
    "#f032e6", "#bcf60c", "#008080", "#9a6324", "#800000", "#808000",
    "#000075", "#e6beff", "#aaffc3", "#808080",
]


def _color(i):
    return PALETTE[i % len(PALETTE)]


def plot_clusters_map(clusters, centers, lat_col, lon_col, output_file):
    """Salva um PNG com todos os grupos (cor por grupo) e seus centros numerados."""
    fig, ax = plt.subplots(figsize=(12, 10))
    for cluster_id, group in clusters.items():
        color = _color(cluster_id)
        ax.scatter(
            group[lon_col], group[lat_col], s=25, color=color, alpha=0.8,
            edgecolors="white", linewidths=0.3,
            label=f"Grupo {cluster_id} ({len(group)} clientes)",
        )
    for _, row in centers.iterrows():
        cid = int(row["cluster"])
        ax.annotate(
            str(cid), (row[lon_col], row[lat_col]),
            fontsize=12, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=_color(cid), alpha=0.95),
        )
    ax.set_title(f"Mapa completo dos grupos ({len(clusters)} grupos)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=0.3)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8, title="Grupos")
    fig.tight_layout()
    fig.savefig(output_file, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_clusters_html(clusters, lat_col, lon_col, output_file):
    """Salva um mapa interativo (HTML) com folium; ignora se folium não estiver instalado."""
    try:
        import folium
    except ImportError:
        logging.warning("folium não instalado (pip install folium); mapa HTML não gerado.")
        return
    all_groups = pd.concat(clusters.values())
    m = folium.Map(
        location=[all_groups[lat_col].mean(), all_groups[lon_col].mean()],
        zoom_start=12,
    )
    for cluster_id, group in clusters.items():
        layer = folium.FeatureGroup(name=f"Grupo {cluster_id} ({len(group)})")
        for _, row in group.iterrows():
            label = row.get("cliente", row.get("codigo", ""))
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]], radius=5,
                color=_color(cluster_id), fill=True, fill_opacity=0.85,
                tooltip=f"Grupo {cluster_id} - {label}",
            ).add_to(layer)
        layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([
        [all_groups[lat_col].min(), all_groups[lon_col].min()],
        [all_groups[lat_col].max(), all_groups[lon_col].max()],
    ])
    m.save(str(output_file))


def _save_maps(clusters, centers, lat_col, lon_col, output_dir, config):
    if not config.get("plot_map", True):
        return
    png = output_dir / "mapa_grupos.png"
    plot_clusters_map(clusters, centers, lat_col, lon_col, png)
    print(f"Mapa dos grupos salvo em {png}")
    if config.get("plot_map_html", True):
        html = output_dir / "mapa_grupos.html"
        plot_clusters_html(clusters, lat_col, lon_col, html)
        if html.exists():
            print(f"Mapa interativo salvo em {html}")


def _choose_k(features, config):
    n = len(features)
    min_k = max(2, int(config.get("min_clusters", 2)))
    max_k = min(int(config.get("max_clusters", 10)), n - 1)
    if max_k < min_k:
        return 1, None

    scores = {}
    for k in range(min_k, max_k + 1):
        model = KMeans(
            n_clusters=k,
            random_state=int(config.get("random_state", 42)),
            n_init=int(config.get("n_init", 10)),
            max_iter=int(config.get("max_iter", 300)),
        )
        labels = model.fit_predict(features)
        if len(set(labels)) > 1:
            scores[k] = float(silhouette_score(features, labels))
    if not scores:
        return min_k, None
    best_k = max(scores, key=scores.get)
    return best_k, scores


def cluster_clients(df, config=None, output_dir=None):
    config = config or {}
    output_dir = Path(output_dir or "output/grupos")
    output_dir.mkdir(parents=True, exist_ok=True)

    lat_col = config.get("latitude_column", "latitude")
    lon_col = config.get("longitude_column", "longitude")
    required = [lat_col, lon_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas de coordenadas ausentes: {missing}")

    result = df.copy()
    result[required] = result[required].apply(pd.to_numeric, errors="coerce")
    result = result.dropna(subset=required).copy()
    if result.empty:
        raise ValueError("Nenhum cliente possui coordenadas válidas.")
    if len(result) < 2:
        result["cluster"] = 0
        result.to_csv(output_dir / "cluster_0.csv", index=False, encoding="utf-8-sig")
        single_center = pd.DataFrame(
            {"cluster": [0], lat_col: [result[lat_col].iloc[0]], lon_col: [result[lon_col].iloc[0]]}
        )
        _save_maps({0: result}, single_center, lat_col, lon_col, output_dir, config)
        return {0: result}

    features = result[required]
    auto_k = bool(config.get("auto_clusters", True))
    if auto_k:
        k, scores = _choose_k(
            features,
            {
                **config,
                "min_clusters": config.get("min_clusters", 2),
                "max_clusters": config.get("max_clusters", 10),
            },
        )
    else:
        k = int(config.get("n_clusters", 5))
        scores = None

    k = max(1, min(k, len(result)))
    model = KMeans(
        n_clusters=k,
        random_state=int(config.get("random_state", 42)),
        n_init=int(config.get("n_init", 10)),
        max_iter=int(config.get("max_iter", 300)),
    )
    result["cluster"] = model.fit_predict(features)

    result.to_csv(output_dir / "clientes_agrupados.csv", index=False, encoding="utf-8-sig")
    clusters = {}
    for cluster_id in sorted(result["cluster"].unique()):
        group = result[result["cluster"] == cluster_id].copy()
        group.to_csv(output_dir / f"cluster_{cluster_id}.csv", index=False, encoding="utf-8-sig")
        clusters[int(cluster_id)] = group

    centers = pd.DataFrame(model.cluster_centers_, columns=required)
    centers.insert(0, "cluster", range(k))
    centers.to_csv(output_dir / "centros_clusters.csv", index=False, encoding="utf-8-sig")

    if scores:
        pd.DataFrame(
            [{"k": key, "silhouette": value} for key, value in scores.items()]
        ).to_csv(output_dir / "avaliacao_k.csv", index=False, encoding="utf-8-sig")

    print(f"Quantidade de grupos selecionada: {k}")
    if scores:
        print(f"Melhor silhouette: {scores[k]:.4f}")

    _save_maps(clusters, centers, lat_col, lon_col, output_dir, config)
    return clusters