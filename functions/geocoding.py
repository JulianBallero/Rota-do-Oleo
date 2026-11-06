
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from pathlib import Path

# ==============================
# CONFIGURATION
# ==============================

INPUT_FILE = "../dataset/clientes.csv"
OUTPUT_FILE = "../output/clientes_coordenadas.csv"

ADDRESS_COLUMN = "endereco"

# Paraná, Brazil
COUNTRY = "Brazil"
REGION = "Paraná"

# ==============================
# INITIALIZATION
# ==============================

Path("./output").mkdir(parents=True, exist_ok=True)

geolocator = Nominatim(
    user_agent="rota_do_oleo_geocoder"
)

geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1,
    error_wait_seconds=2,
    max_retries=2,
    swallow_exceptions=True
)

# ==============================
# GEOCODING FUNCTION
# ==============================

def get_coordinates(address):

    if pd.isna(address) or str(address).strip() == "":
        return None, None

    try:
        search_address = f"{address}, {REGION}, {COUNTRY}"

        location = geocode(
            search_address,
            country_codes="br",
            addressdetails=True
        )

        if location:
            return location.latitude, location.longitude

        print(f"Address not found: {address}")
        return None, None

    except Exception as error:
        print(f"Error: {address} - {error}")
        return None, None


# ==============================
# MAIN
# ==============================

def main():

    # Read customer CSV
    df = pd.read_csv(INPUT_FILE)

    # Validate address column
    if ADDRESS_COLUMN not in df.columns:
        raise ValueError(
            f"Column '{ADDRESS_COLUMN}' not found in CSV. "
            f"Available columns: {list(df.columns)}"
        )

    print(f"Searching coordinates for {len(df)} customers...")

    # Search coordinates
    coordinates = df[ADDRESS_COLUMN].apply(get_coordinates)

    df["LAT"] = coordinates.apply(lambda x: x[0])
    df["LON"] = coordinates.apply(lambda x: x[1])

    # Save CSV
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # Statistics
    successful = df["LAT"].notna().sum()
    failed = len(df) - successful

    print("\nGeocoding completed!")
    print(f"Total customers: {len(df)}")
    print(f"Successfully geocoded: {successful}")
    print(f"Failed searches: {failed}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
