
import pandas as pd
import random

# Input and output files
input_file = "database-improvisado.csv"
output_file = "clientes-com-coordenadas.csv"

# Read CSV
df = pd.read_csv("dataset/database-improvisado.csv", sep=",", encoding="utf-8")

# Define geographic boundaries
lat_min = -25.334176
lat_max = -25.332935

lon_min = -49.411334
lon_max = -49.397602

# Generate random coordinates for each client
df["latitude"] = [
    random.uniform(lat_min, lat_max)
    for _ in range(len(df))
]

df["longitude"] = [
    random.uniform(lon_min, lon_max)
    for _ in range(len(df))
]

# Save new CSV
df.to_csv("dataset/clientes-com-coordenadas.csv", index=False, encoding="utf-8-sig")

print(f"File generated successfully: {output_file}")
print(df.head())
