
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

# ==========================
# CONFIGURATION
# ==========================

input_file = "./output/grupos/cluster_0.csv"
output_file = "./output/rotas/rota_cluster_0.csv"

# Geographic columns
LAT = "latitude"
LON = "longitude"

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(input_file)

if df.empty:
    raise ValueError("The input CSV is empty.")

# Validate coordinates
df = df.dropna(subset=[LAT, LON]).reset_index(drop=True)

if df.empty:
    raise ValueError("No valid geographic coordinates found.")

# ==========================
# FIND HIGHEST POINT
# ==========================

# Highest latitude = northernmost point
start_index = df[LAT].idxmax()

print("Starting location:")
print(df.loc[start_index])

# ==========================
# NEAREST NEIGHBOR ROUTE
# ==========================

# Convert coordinates to radians for Haversine distance
coordinates = np.radians(df[[LAT, LON]].values)

# Haversine distance (in radians)
nn = NearestNeighbors(
    n_neighbors=len(df),
    metric="haversine",
    algorithm="ball_tree"
)

nn.fit(coordinates)

visited = set()
route = []

current_index = start_index

while len(visited) < len(df):

    visited.add(current_index)
    route.append(current_index)

    # Find nearest neighbors from current location
    distances, indices = nn.kneighbors(
        coordinates[current_index].reshape(1, -1)
    )

    # Select nearest unvisited point
    next_index = None

    for idx in indices[0]:
        if idx not in visited:
            next_index = idx
            break

    if next_index is None:
        break

    current_index = next_index

# ==========================
# CREATE ROUTE CSV
# ==========================

route_df = df.iloc[route].copy()

# Add route order
route_df.insert(
    0,
    "Nova Ordem",
    range(1, len(route_df) + 1)
)

route_df.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)

# ==========================
# RESULTS
# ==========================

print("\nRoute generated successfully!")
print(f"Total locations: {len(route_df)}")
print(f"Starting point: {route_df.iloc[0][LAT]}, {route_df.iloc[0][LON]}")
print(f"Output: {output_file}")

print("\nRoute:")
print(route_df[["Nova Ordem", "Cliente ", LAT, LON]])



