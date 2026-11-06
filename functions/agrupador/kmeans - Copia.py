"""Agrupamento geográfico de clientes com seleção opcional de K por silhouette."""
from pathlib import Path
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


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
    return clusters
