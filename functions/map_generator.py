"""Geração de mapas com os pontos da rota sobrepostos ao mapa-base.

- generate_map:        mapa interativo (HTML, folium) com satélite/ruas.
- generate_static_map: imagem PNG com o mapa-base como fundo e a rota por cima.
"""
import html
import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pandas as pd

TILE_SIZE = 256

BASEMAPS = {
    "satellite": {
        "name": "Imagem de satélite",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Esri, Maxar, Earthstar Geographics",
    },
    "streets": {
        "name": "Mapa de ruas",
        "url": (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        "attr": "Esri",
    },
}

_TILE_CACHE = {}


def find_column(df, candidates, description):
    """Localiza uma coluna ignorando maiúsculas e espaços."""
    columns = {str(col).strip().casefold(): col for col in df.columns}

    for candidate in candidates:
        key = candidate.strip().casefold()
        if key in columns:
            return columns[key]

    raise ValueError(
        f"Coluna de {description} não encontrada. "
        f"Colunas disponíveis: {list(df.columns)}"
    )


def _prepare_route(route_df, lat_col=None, lon_col=None):
    """Valida colunas, converte coordenadas e ordena as paradas."""
    lat_col = lat_col or find_column(
        route_df, ["LAT", "latitude", "lat"], "latitude"
    )
    lon_col = lon_col or find_column(
        route_df, ["LON", "longitude", "lon", "long"], "longitude"
    )
    order_col = find_column(
        route_df, ["Nova Ordem", "nova_ordem", "ordem"], "ordem"
    )
    client_col = find_column(
        route_df, ["Cliente", "cliente", "nome"], "cliente"
    )

    df = route_df.copy()
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df = df.dropna(subset=[lat_col, lon_col])

    if df.empty:
        raise ValueError("Nenhuma coordenada válida para gerar o mapa.")

    df = df.sort_values(order_col).reset_index(drop=True)
    return df, lat_col, lon_col, order_col, client_col


def _fmt_order(value):
    """Mostra a ordem como inteiro quando possível (3 em vez de 3.0)."""
    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else str(value)
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# Mapa interativo (HTML)
# ---------------------------------------------------------------------------
def generate_map(
    route_df,
    filename="rota.html",
    lat_col=None,
    lon_col=None,
    output_dir="./output/graficos",
    basemap="satellite",
):
    """Gera o mapa interativo com trajeto e paradas numeradas sobre o mapa."""
    import folium

    df, lat_col, lon_col, order_col, client_col = _prepare_route(
        route_df, lat_col, lon_col
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pontos = df[[lat_col, lon_col]].values.tolist()

    mapa = folium.Map(
        location=[df[lat_col].mean(), df[lon_col].mean()],
        zoom_start=14,
        tiles=None,
        control_scale=True,
    )

    # Mapas-base: o escolhido fica visível; os demais ficam no seletor.
    ordem_bases = [basemap] + [k for k in BASEMAPS if k != basemap]
    for key in ordem_bases:
        cfg = BASEMAPS.get(key)
        if cfg is None:
            continue
        folium.TileLayer(
            tiles=cfg["url"],
            attr=cfg["attr"],
            name=cfg["name"],
            overlay=False,
            control=True,
            show=(key == basemap),
        ).add_to(mapa)
    folium.TileLayer(
        "OpenStreetMap",
        name="Mapa convencional",
        overlay=False,
        control=True,
        show=False,
    ).add_to(mapa)

    # Camada do trajeto (desenhada primeiro, para ficar abaixo dos pontos).
    camada_rota = folium.FeatureGroup(name="Trajeto da rota", show=True)
    if len(pontos) > 1:
        # Contorno branco + linha colorida: boa leitura sobre o satélite.
        folium.PolyLine(
            pontos, color="white", weight=7, opacity=0.9
        ).add_to(camada_rota)
        folium.PolyLine(
            pontos,
            color="#1f5fff",
            weight=4,
            opacity=0.95,
            tooltip="Trajeto da rota",
        ).add_to(camada_rota)
    camada_rota.add_to(mapa)

    # Camada dos pontos, sobrepostos ao mapa e à linha.
    camada_pontos = folium.FeatureGroup(name="Paradas", show=True)
    ultimo = len(df) - 1
    for i, row in df.iterrows():
        ordem = _fmt_order(row[order_col])
        cliente = html.escape(str(row[client_col]))

        if i == 0:
            cor = "#1e9e3a"  # início
        elif i == ultimo and len(df) > 1:
            cor = "#111111"  # fim
        else:
            cor = "#e6194b"

        icone = folium.DivIcon(
            icon_size=(28, 28),
            icon_anchor=(14, 14),
            html=(
                f'<div style="background:{cor};color:#fff;width:28px;'
                "height:28px;line-height:24px;border:2px solid #fff;"
                "border-radius:50%;text-align:center;font:bold 11px Arial;"
                'box-shadow:0 0 4px rgba(0,0,0,.7);">'
                f"{ordem}</div>"
            ),
        )

        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            icon=icone,
            popup=folium.Popup(
                f"<b>Cliente:</b> {cliente}<br><b>Ordem:</b> {ordem}",
                max_width=300,
            ),
            tooltip=f"Parada {ordem} - {cliente}",
            z_index_offset=1000,
        ).add_to(camada_pontos)
    camada_pontos.add_to(mapa)

    mapa.fit_bounds(pontos, padding=(30, 30))
    folium.LayerControl(collapsed=False).add_to(mapa)

    filepath = output_dir / filename
    mapa.save(str(filepath))
    logging.info("Mapa interativo salvo em: %s", filepath)

    return mapa


# ---------------------------------------------------------------------------
# Mapa estático (PNG) com o mapa-base como fundo
# ---------------------------------------------------------------------------
def _latlon_to_tile_xy(lat, lon, zoom):
    """Converte lat/lon em coordenadas de tile (Web Mercator), em ponto flutuante."""
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def _fetch_tile(basemap, zoom, x, y, timeout=10):
    """Baixa um tile (com cache em memória). Retorna imagem PIL ou None."""
    import requests
    from PIL import Image

    key = (basemap, zoom, x, y)
    if key in _TILE_CACHE:
        return _TILE_CACHE[key]

    url = BASEMAPS[basemap]["url"].format(z=zoom, x=x, y=y)
    try:
        resp = requests.get(
            url, timeout=timeout, headers={"User-Agent": "rota_do_oleo_app"}
        )
        resp.raise_for_status()
        tile = Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception as exc:  # rede indisponível, tile ausente, etc.
        logging.debug("Falha ao baixar tile %s/%s/%s: %s", zoom, x, y, exc)
        return None

    _TILE_CACHE[key] = tile
    return tile


def _build_basemap_image(lat_min, lat_max, lon_min, lon_max, basemap,
                         max_tiles=8, timeout=10):
    """Monta o mosaico de tiles que cobre a área.

    Retorna (imagem, zoom, x_tile_inicial, y_tile_inicial).
    """
    from PIL import Image

    # Maior zoom cujo mosaico caiba em max_tiles x max_tiles.
    for zoom in range(19, 0, -1):
        x0, y1 = _latlon_to_tile_xy(lat_min, lon_min, zoom)
        x1, y0 = _latlon_to_tile_xy(lat_max, lon_max, zoom)
        tx0, tx1 = int(math.floor(x0)), int(math.floor(x1))
        ty0, ty1 = int(math.floor(y0)), int(math.floor(y1))
        if (tx1 - tx0 + 1) <= max_tiles and (ty1 - ty0 + 1) <= max_tiles:
            break

    coords = [
        (tx, ty)
        for ty in range(ty0, ty1 + 1)
        for tx in range(tx0, tx1 + 1)
    ]

    with ThreadPoolExecutor(max_workers=8) as pool:
        tiles = list(
            pool.map(
                lambda c: _fetch_tile(basemap, zoom, c[0], c[1], timeout),
                coords,
            )
        )

    failed = sum(t is None for t in tiles)
    if failed == len(tiles):
        raise RuntimeError(
            "Não foi possível baixar o mapa-base (verifique a conexão)."
        )
    if failed:
        logging.warning(
            "%s de %s tiles do mapa-base não foram baixados; "
            "a imagem terá áreas em cinza.",
            failed,
            len(tiles),
        )

    width = (tx1 - tx0 + 1) * TILE_SIZE
    height = (ty1 - ty0 + 1) * TILE_SIZE
    mosaic = Image.new("RGB", (width, height), (40, 40, 40))
    for (tx, ty), tile in zip(coords, tiles):
        if tile is not None:
            mosaic.paste(tile, ((tx - tx0) * TILE_SIZE, (ty - ty0) * TILE_SIZE))

    return mosaic, zoom, tx0, ty0


def generate_static_map(
    route_df,
    output_file,
    lat_col=None,
    lon_col=None,
    basemap="satellite",
    dpi=150,
    max_tiles=8,
    timeout=10,
):
    """Salva um PNG com o mapa-base ao fundo e trajeto/paradas sobrepostos.

    Levanta RuntimeError se o mapa-base não puder ser baixado, para que o
    chamador possa usar um gráfico sem fundo como alternativa.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if basemap not in BASEMAPS:
        raise ValueError(
            f"Mapa-base inválido: {basemap!r}. Opções: {list(BASEMAPS)}"
        )

    df, lat_col, lon_col, order_col, _ = _prepare_route(
        route_df, lat_col, lon_col
    )

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Área com folga ao redor dos pontos (mínimo para rotas de 1 ponto).
    lat_span = max(df[lat_col].max() - df[lat_col].min(), 0.002)
    lon_span = max(df[lon_col].max() - df[lon_col].min(), 0.002)
    pad_lat, pad_lon = lat_span * 0.08, lon_span * 0.08
    lat_min = df[lat_col].min() - pad_lat
    lat_max = df[lat_col].max() + pad_lat
    lon_min = df[lon_col].min() - pad_lon
    lon_max = df[lon_col].max() + pad_lon

    mosaic, zoom, tx0, ty0 = _build_basemap_image(
        lat_min, lat_max, lon_min, lon_max, basemap, max_tiles, timeout
    )

    def to_px(lat, lon):
        x, y = _latlon_to_tile_xy(lat, lon, zoom)
        return (x - tx0) * TILE_SIZE, (y - ty0) * TILE_SIZE

    xs, ys = zip(*(to_px(a, b) for a, b in zip(df[lat_col], df[lon_col])))
    px_left, px_bottom = to_px(lat_min, lon_min)
    px_right, px_top = to_px(lat_max, lon_max)
    view_w = abs(px_right - px_left)
    view_h = abs(px_bottom - px_top)

    fig_w = 10
    fig_h = max(4, min(14, fig_w * view_h / view_w))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    ax.imshow(mosaic, extent=(0, mosaic.width, mosaic.height, 0), zorder=0)
    ax.set_xlim(px_left, px_right)
    ax.set_ylim(px_bottom, px_top)  # eixo Y de imagem: norte em cima
    ax.axis("off")

    # Trajeto (contorno branco + linha colorida) e paradas por cima.
    if len(df) > 1:
        ax.plot(xs, ys, color="white", linewidth=4.5, alpha=0.9, zorder=2)
        ax.plot(xs, ys, color="#1f5fff", linewidth=2.2, zorder=3)

    cores = ["#e6194b"] * len(df)
    cores[0] = "#1e9e3a"
    if len(df) > 1:
        cores[-1] = "#111111"

    ax.scatter(
        xs, ys, s=170, c=cores, edgecolors="white", linewidths=1.5, zorder=4
    )
    for x, y, ordem in zip(xs, ys, df[order_col]):
        ax.annotate(
            _fmt_order(ordem), (x, y), ha="center", va="center",
            fontsize=6.5, fontweight="bold", color="white", zorder=5,
        )

    ax.set_title("Rota aproximada de coleta", fontsize=12)
    ax.text(
        0.995, 0.005, f"Imagem: {BASEMAPS[basemap]['attr']}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=6,
        color="white",
        bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.5, ec="none"),
        zorder=6,
    )

    fig.tight_layout()
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logging.info("Mapa estático salvo em: %s", output_file)

    return output_file
