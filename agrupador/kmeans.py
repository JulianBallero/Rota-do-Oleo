
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import os

# ==========================
# CONFIGURATION
# ==========================

input_file = "./dataset/clientes-com-coordenadas.csv"
output_file = "./output/clientes-agrupados.csv"

# Choose the number of clusters
K = 5

# Folder to save individual groups
output_folder = "./output/grupos"

# ==========================
# LOAD DATA
# ==========================

df = pd.read_csv(input_file)

X = df[["latitude", "longitude"]]

# ==========================
# K-MEANS
# ==========================

kmeans = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=10
)

df["cluster"] = kmeans.fit_predict(X)

# ==========================
# SAVE COMPLETE CSV
# ==========================

df.to_csv("./output/clientes-agrupados.csv", index=False, encoding="utf-8-sig")

print(f"Complete file saved: {output_file}")

# ==========================
# SAVE INDIVIDUAL CLUSTERS
# ==========================

# Create output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

for cluster_id in range(K):

    # Filter clients belonging to this cluster
    group = df[df["cluster"] == cluster_id]

    # Define output filename
    group_file = os.path.join(
        output_folder,
        f"cluster_{cluster_id}.csv"
    )

    # Save group
    group.to_csv(
        group_file,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Cluster {cluster_id}: "
        f"{len(group)} clients saved to {group_file}"
    )

# ==========================
# CLUSTER CENTERS
# ==========================

centers = pd.DataFrame(
    kmeans.cluster_centers_,
    columns=["latitude", "longitude"]
)

print("\nCluster centers:")
print(centers)

# ==========================
# VISUALIZATION
# ==========================

plt.figure(figsize=(10, 7))

plt.scatter(
    df["longitude"],
    df["latitude"],
    c=df["cluster"],
    cmap="viridis",
    s=40
)

plt.scatter(
    centers["longitude"],
    centers["latitude"],
    marker="X",
    s=200,
    c="red",
    label="Cluster centers"
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title(f"Geographic K-Means - {K} Clusters")
plt.legend()
plt.grid(True)

plt.show()
