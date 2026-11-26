"""Geração de rota aproximada pelo vizinho mais próximo (distância Haversine)."""
from pathlib import Path
import numpy as np
import pandas as pd


def _haversine_km(point, candidates):
    lat1, lon1 = np.radians(point)
    lat2 = np.radians(candidates[:, 0])
    lon2 = np.radians(candidates[:, 1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def generate_route(df, config=None):
    config = config or {}
    lat_col = config.get("latitude_column", "latitude")
    lon_col = config.get("longitude_column", "longitude")
    missing = [c for c in (lat_col, lon_col) if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas de coordenadas ausentes para roteirização: {missing}")

    route_data = df.copy()
    route_data[lat_col] = pd.to_numeric(route_data[lat_col], errors="coerce")
    route_data[lon_col] = pd.to_numeric(route_data[lon_col], errors="coerce")
    route_data = route_data.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)
    if route_data.empty:
        raise ValueError("O grupo não possui coordenadas válidas.")

    coords = route_data[[lat_col, lon_col]].to_numpy(dtype=float)
    start_mode = config.get("start_point", "highest_latitude")
    if start_mode == "highest_latitude":
        current = int(np.argmax(coords[:, 0]))
    else:
        current = 0

    remaining = set(range(len(route_data)))
    order = []
    while remaining:
        order.append(current)
        remaining.remove(current)
        if remaining:
            candidates_idx = np.array(sorted(remaining), dtype=int)
            distances = _haversine_km(coords[current], coords[candidates_idx])
            current = int(candidates_idx[int(np.argmin(distances))])

    route = route_data.iloc[order].copy().reset_index(drop=True)
    route.insert(0, "Nova Ordem", range(1, len(route) + 1))
    if bool(config.get("return_to_start", False)) and len(route) > 1:
        first = route.iloc[[0]].copy()
        first.iloc[0, first.columns.get_loc("Nova Ordem")] = len(route) + 1
        route = pd.concat([route, first], ignore_index=True)
    return route


def plot_route(route_df, output_file, config=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    config = config or {}
    lat_col = config.get("latitude_column", "latitude")
    lon_col = config.get("longitude_column", "longitude")
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.plot(route_df[lon_col], route_df[lat_col], marker="o", linewidth=1)
    for _, row in route_df.iterrows():
        ax.annotate(str(row["Nova Ordem"]), (row[lon_col], row[lat_col]), fontsize=7)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Rota aproximada de coleta")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
