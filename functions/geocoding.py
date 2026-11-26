"""Geocodificação opcional de clientes usando Nominatim."""
from pathlib import Path
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


def geocode_csv(input_file, output_file, config=None):
    config = config or {}
    address_column = config.get("address_column", "endereco")
    region = config.get("region", "Paraná")
    country = config.get("country", "Brazil")
    user_agent = config.get("user_agent", "rota_do_oleo_app")
    timeout = int(config.get("timeout", 10))

    input_file, output_file = Path(input_file), Path(output_file)
    df = pd.read_csv(input_file, encoding="utf-8-sig")
    if address_column not in df.columns:
        raise ValueError(
            f"Coluna de endereço '{address_column}' não encontrada. "
            f"Colunas disponíveis: {list(df.columns)}"
        )

    geolocator = Nominatim(user_agent=user_agent, timeout=timeout)
    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1,
        max_retries=int(config.get("retry_attempts", 2)),
        error_wait_seconds=2,
        swallow_exceptions=True,
    )

    def locate(value):
        if pd.isna(value) or not str(value).strip():
            return (None, None)
        result = geocode(f"{value}, {region}, {country}", country_codes="br")
        return (result.latitude, result.longitude) if result else (None, None)

    coords = df[address_column].apply(locate)
    df["LAT"] = coords.map(lambda item: item[0])
    df["LON"] = coords.map(lambda item: item[1])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    return df
