
import folium
import os
import pandas as pd


def find_column(df, candidates, description):
    """Localiza uma coluna ignorando maiúsculas e espaços."""
    columns = {
        str(col).strip().casefold(): col
        for col in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().casefold()
        if key in columns:
            return columns[key]

    raise ValueError(
        f"Coluna de {description} não encontrada. "
        f"Colunas disponíveis: {list(df.columns)}"
    )


def generate_map(
    route_df,
    filename="rota.html",
    lat_col=None,
    lon_col=None
):

    output_dir = "./output/graficos"
    os.makedirs(output_dir, exist_ok=True)

    # Identificar colunas de coordenadas
    lat_col = lat_col or find_column(
        route_df,
        ["LAT", "latitude", "lat"],
        "latitude"
    )

    lon_col = lon_col or find_column(
        route_df,
        ["LON", "longitude", "lon", "long"],
        "longitude"
    )

    # Identificar ordem e cliente
    order_col = find_column(
        route_df,
        ["Nova Ordem", "nova_ordem", "ordem"],
        "ordem"
    )

    client_col = find_column(
        route_df,
        ["Cliente", "cliente", "nome"],
        "cliente"
    )

    # Preparar dados
    route_df = route_df.copy()

    route_df[lat_col] = pd.to_numeric(
        route_df[lat_col], errors="coerce"
    )

    route_df[lon_col] = pd.to_numeric(
        route_df[lon_col], errors="coerce"
    )

    route_df = route_df.dropna(
        subset=[lat_col, lon_col]
    )

    if route_df.empty:
        raise ValueError("Nenhuma coordenada válida para gerar o mapa.")
    
    

    route_df = route_df.sort_values(order_col)

    # Centro do mapa
    center_lat = route_df[lat_col].mean()
    center_lon = route_df[lon_col].mean()

    mapa = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles=None
    )

    # Imagem de satélite da Esri
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/World_Imagery/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri, Maxar, Earthstar Geographics",
        name="Imagem de satélite",
        overlay=False,
        control=True
    ).add_to(mapa)

    # Camada de ruas da Esri
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/World_Street_Map/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Mapa de ruas",
        overlay=False,
        control=True
    ).add_to(mapa)

    folium.LayerControl().add_to(mapa)

    # Imagem de satélite
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/World_Imagery/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri, Maxar, Earthstar Geographics",
        name="Satélite",
        overlay=False,
        control=True
    ).add_to(mapa)

    # Mapa convencional
    folium.TileLayer(
        "OpenStreetMap",
        name="Mapa convencional",
        overlay=False,
        control=True
    ).add_to(mapa)

    pontos = []

    # Adicionar clientes
    for _, row in route_df.iterrows():

        lat = row[lat_col]
        lon = row[lon_col]

        pontos.append([lat, lon])

        folium.Marker(
            location=[lat, lon],
            popup=(
                f"Cliente: {row[client_col]}<br>"
                f"Ordem: {row[order_col]}"
            ),
            tooltip=f"Parada {row[order_col]}",
            icon=folium.Icon(
                color="red",
                icon="info-sign"
            )
        ).add_to(mapa)

    # Desenhar rota
    if len(pontos) > 1:
        folium.PolyLine(
            pontos,
            color="blue",
            weight=4,
            opacity=0.8,
            tooltip="Trajeto da rota"
        ).add_to(mapa)

    # Ajustar enquadramento
    mapa.fit_bounds(pontos)

    # Controle de camadas
    folium.LayerControl().add_to(mapa)

    # Salvar mapa
    filepath = os.path.join(output_dir, filename)
    mapa.save(filepath)

    print(f"Mapa interativo salvo em: {filepath}")

    return mapa
