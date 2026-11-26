
import logging
import pandas as pd

from pathlib import Path

<<<<<<< Updated upstream
from geocoding import geocode_csv
from kmeans import cluster_clients
from knn import generate_route, plot_route
=======
import pandas as pd
import yaml

from functions.agrupador.kmeans import cluster_clients
from functions.roteirizador.knn import generate_route, plot_route
from functions.geocoding import geocode_csv
from functions.map_generator import generate_map, generate_static_map
>>>>>>> Stashed changes


# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "parameters.yaml"

INPUT_FILE = BASE_DIR / "dataset" / "clientes.csv"

OUTPUT_DIR = BASE_DIR / "output"

GROUPS_DIR = OUTPUT_DIR / "grupos"
ROUTES_DIR = OUTPUT_DIR / "rotas"
GRAPHS_DIR = OUTPUT_DIR / "graficos"

LOG_FILE = OUTPUT_DIR / "rota_do_oleo.log"

MAX_CLIENTS = 70


# ==========================================
# LOGGING
# ==========================================

def setup_logging():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


# ==========================================
# CARREGAR CONFIGURAÇÕES
# ==========================================

def load_config():

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config or {}


# ==========================================
# VALIDAR ARQUIVO DE ENTRADA
# ==========================================

def validate_input():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "ordem",
        "código",
        "cliente"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {missing}"
        )

    if len(df) == 0:
        raise ValueError("O arquivo CSV está vazio.")

<<<<<<< Updated upstream
    if len(df) > MAX_CLIENTS:
        raise ValueError(
            f"Limite de {MAX_CLIENTS} clientes excedido. "
            f"Arquivo contém {len(df)} clientes."
        )

    logging.info(f"{len(df)} clientes encontrados.")

    return df


# ==========================================
# PREPARAR DIRETÓRIOS
# ==========================================

def create_directories():

    for directory in [
        GROUPS_DIR,
        ROUTES_DIR,
        GRAPHS_DIR
    ]:
        directory.mkdir(parents=True, exist_ok=True)


# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================

def main():

    setup_logging()

    logging.info("====================================")
    logging.info("INICIANDO ROTA DO ÓLEO")
    logging.info("====================================")

    try:

        # 1. Carregar configurações
        config = load_config()

        # 2. Criar diretórios
        create_directories()

        # 3. Validar entrada
        df = validate_input()

        # 4. Geocoding
        if config.get("geocoding", {}).get("enabled", True):

            logging.info("Iniciando geocoding...")

            coordinates_file = (
                OUTPUT_DIR / "clientes_coordenadas.csv"
            )

            geocode_csv(
                input_file=INPUT_FILE,
                output_file=coordinates_file,
                config=config.get("geocoding", {})
            )

            df = pd.read_csv(coordinates_file)

        # 5. Validar coordenadas
        coordinate_columns = ["LAT", "LON"]

        for col in coordinate_columns:
            if col not in df.columns:
                raise ValueError(
                    f"Coluna de coordenada ausente: {col}"
                )

        if df[coordinate_columns].isnull().any().any():
            raise ValueError(
                "Existem clientes sem coordenadas válidas."
            )

        logging.info("Coordenadas validadas.")

        # 6. K-Means
        logging.info("Iniciando agrupamento K-Means...")

        clusters = cluster_clients(
            df=df,
            config=config.get("clustering", {}),
            output_dir=GROUPS_DIR
=======
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
>>>>>>> Stashed changes
        )

        logging.info(
            f"{len(clusters)} grupos gerados."
        )

        # 7. KNN - Gerar rotas para cada cluster
        logging.info("Iniciando geração das rotas...")

        for cluster_id, cluster_df in clusters.items():

            logging.info(
                f"Calculando rota do cluster {cluster_id}..."
            )

            route_df = generate_route(
                df=cluster_df,
                config=config.get("routing", {})
            )

            # Salvar rota
            route_file = (
                ROUTES_DIR / f"rota_cluster_{cluster_id}.csv"
            )

            route_df.to_csv(
                route_file,
                index=False,
                encoding="utf-8-sig"
            )

            # Gerar gráfico
            graph_file = (
                GRAPHS_DIR / f"rota_cluster_{cluster_id}.png"
            )

            plot_route(
                route_df=route_df,
                output_file=graph_file
            )

            logging.info(
                f"Rota do cluster {cluster_id} concluída."
            )

        logging.info("====================================")
        logging.info("PROCESSAMENTO CONCLUÍDO COM SUCESSO")
        logging.info("====================================")

    except Exception as e:

        logging.exception(
            f"Erro durante o processamento: {e}"
        )


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()