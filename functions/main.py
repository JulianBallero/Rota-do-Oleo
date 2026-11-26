import logging
from pathlib import Path

import pandas as pd
import yaml

from functions.agrupador.kmeans import cluster_clients
from functions.roteirizador.knn import generate_route, plot_route
from functions.geocoding import geocode_csv
from functions.map_generator import (
    generate_map,
    generate_static_map,
    open_maps_in_browser,
)


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = BASE_DIR / "Parameters.yaml"


def load_config():
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Configuração não encontrada: {CONFIG_FILE}")
    with CONFIG_FILE.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def resolve_path(value):
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def normalize_columns(df):
    """Remove espaços acidentais e padroniza nomes conhecidos sem acentos."""
    aliases = {
        "latitude": "latitude",
        "lat": "latitude",
        "longitude": "longitude",
        "lon": "longitude",
        "long": "longitude",
        "cliente": "cliente",
        "codigo": "codigo",
        "ordem": "ordem",
    }
    rename = {}
    for column in df.columns:
        cleaned = str(column).strip()
        key = cleaned.casefold()
        if key in aliases:
            rename[column] = aliases[key]
        elif key == "código":
            rename[column] = "codigo"
    return df.rename(columns=rename)


def load_input(config):
    input_cfg = config.get("input", {})
    input_file = resolve_path(
        input_cfg.get("file", "dataset/clientes-com-coordenadas.csv")
    )

    if not input_file.is_file():
        raise FileNotFoundError(
            f"CSV de entrada não encontrado: {input_file}\n"
            "Ajuste input.file em Parameters.yaml para apontar para o CSV existente."
        )

    df = pd.read_csv(
        input_file,
        sep=input_cfg.get("separator", ","),
        encoding=input_cfg.get("encoding", "utf-8-sig"),
    )
    df = normalize_columns(df)

    if df.empty:
        raise ValueError(f"O CSV está vazio: {input_file}")

    max_clients = int(input_cfg.get("max_clients", 10000))
    if len(df) > max_clients:
        raise ValueError(
            f"O CSV possui {len(df)} registros, acima do limite configurado "
            f"({max_clients})."
        )

    return df, input_file


def main():
    config = load_config()

    output_cfg = config.get("output", {})
    output_dir = resolve_path(output_cfg.get("directory", "output"))
    groups_dir = resolve_path(output_cfg.get("clusters_directory", "output/grupos"))
    routes_dir = resolve_path(output_cfg.get("routes_directory", "output/rotas"))
    graphs_dir = resolve_path(output_cfg.get("graphs_directory", "output/graficos"))

    for folder in (output_dir, groups_dir, routes_dir, graphs_dir):
        folder.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(
            logging,
            config.get("logging", {}).get("level", "INFO").upper(),
            logging.INFO,
        ),
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                output_dir / "rota_do_oleo.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )

    logging.info("Iniciando Rota do Óleo")
    df, input_file = load_input(config)
    logging.info("CSV carregado: %s (%s clientes)", input_file, len(df))

    geo_cfg = config.get("geocoding", {})
    lat_col = config.get("clustering", {}).get("latitude_column", "latitude")
    lon_col = config.get("clustering", {}).get("longitude_column", "longitude")

    # Geocodifica somente se explicitamente habilitado e se as coordenadas
    # não estiverem completas.
    if geo_cfg.get("enabled", False) and not {lat_col, lon_col}.issubset(df.columns):
        logging.info("Coordenadas ausentes; iniciando geocodificação")
        address_input = resolve_path(geo_cfg.get("input_file", input_file))
        geo_output = output_dir / "clientes_coordenadas.csv"
        df = normalize_columns(geocode_csv(address_input, geo_output, geo_cfg))

    missing_cols = [c for c in (lat_col, lon_col) if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Colunas de coordenadas não encontradas: {missing_cols}. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

    invalid = df[[lat_col, lon_col]].isna().any(axis=1)
    if invalid.any():
        logging.warning(
            "%s registros sem coordenadas válidas serão ignorados.",
            int(invalid.sum()),
        )
        df = df.loc[~invalid].copy()

    if df.empty:
        raise ValueError("Nenhum cliente restante com coordenadas válidas.")

    clusters = cluster_clients(df, config.get("clustering", {}), groups_dir)
    logging.info("%s grupos criados", len(clusters))

    route_cfg = config.get("routing", {})
    # Mapa-base dos mapas: "satellite" (padrão) ou "streets".
    basemap = config.get("map", {}).get("basemap", "satellite")
    html_files = []  # mapas HTML gerados, para abrir no navegador ao final

    for cluster_id, cluster_df in clusters.items():
        route = generate_route(cluster_df, route_cfg)

        route_file = routes_dir / f"rota_cluster_{cluster_id}.csv"
        route.to_csv(route_file, index=False, encoding="utf-8-sig")

        # Gráfico estático (PNG): pontos e trajeto sobrepostos ao mapa-base.
        # Se o mapa-base não puder ser baixado (sem internet, por exemplo),
        # cai para o gráfico simples sem fundo.
        png_file = graphs_dir / f"rota_cluster_{cluster_id}.png"
        try:
            generate_static_map(
                route,
                png_file,
                lat_col=lat_col,
                lon_col=lon_col,
                basemap=basemap,
            )
        except Exception as exc:
            logging.warning(
                "Cluster %s: mapa-base indisponível (%s); "
                "gerando gráfico simples sem fundo.",
                cluster_id,
                exc,
            )
            plot_route(route, png_file, route_cfg)

        # Mapa interativo (HTML) com os pontos sobrepostos ao mapa.
        map_file = f"rota_cluster_{cluster_id}.html"
        logging.debug(
            "Cluster %s: %s pontos; colunas: %s",
            cluster_id,
            len(route),
            route.columns.tolist(),
        )

        generate_map(
            route,
            filename=map_file,
            lat_col=lat_col,
            lon_col=lon_col,
            output_dir=graphs_dir,
            basemap=basemap,
        )
        html_files.append(graphs_dir / map_file)

        logging.info(
            "Cluster %s: %s paradas; CSV: %s; mapa interativo: %s",
            cluster_id,
            len(route),
            route_file,
            graphs_dir / map_file,
        )

    logging.info("Processamento concluído. Resultados em %s", output_dir)

    # Pergunta no console e abre os mapas (grupos primeiro, depois as rotas).
    if config.get("map", {}).get("open_in_browser", True):
        open_maps_in_browser([groups_dir / "mapa_grupos.html", *html_files])


if __name__ == "__main__":
    main()