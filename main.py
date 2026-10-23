import ast
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Altere este identificador para analisar outra instancia do CSV.
INSTANCE_ID = 0
K_MAX = 10

arquivo = Path(__file__).with_name('tsp_dataset.csv')

# Le apenas a instancia solicitada, sem carregar todo o CSV na memoria.
with arquivo.open('r', encoding='utf-8', newline='') as f:
    leitor = csv.DictReader(f)
    instancia = next((linha for linha in leitor
                      if int(linha['instance_id']) == INSTANCE_ID), None)

if instancia is None:
    raise ValueError(f'Instancia {INSTANCE_ID} nao encontrada no CSV.')

X = np.asarray(ast.literal_eval(instancia['city_coordinates']), dtype=float)
n = len(X)
if n < 3:
    raise ValueError('Sao necessarias pelo menos 3 cidades para calcular o Silhouette Score.')

# O Silhouette Score requer 2 <= numero de grupos <= numero de pontos - 1.
ks = range(2, min(K_MAX, n - 1) + 1)
resultados = []
modelos = {}

for k in ks:
    modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
    grupos = modelo.fit_predict(X)
    if len(np.unique(grupos)) < 2 or len(np.unique(grupos)) >= n:
        continue
    score = silhouette_score(X, grupos)
    resultados.append((k, score))
    modelos[k] = modelo
    print(f'K={k:2d} | Silhouette Score={score:.4f}')

if not resultados:
    raise ValueError('Nao foi possivel obter agrupamentos validos.')

k_ideal, melhor_score = max(resultados, key=lambda item: item[1])
melhor_modelo = modelos[k_ideal]
grupo = melhor_modelo.labels_
centros = melhor_modelo.cluster_centers_

print(f'\nInstancia: {INSTANCE_ID} | Cidades: {n}')
print(f'Numero recomendado de grupos: {k_ideal}')
print(f'Melhor Silhouette Score: {melhor_score:.4f}')
for j in range(k_ideal):
    print(f'Grupo {j + 1}: {np.sum(grupo == j)} cidades; centroide {centros[j]}')

fig, eixos = plt.subplots(1, 2, figsize=(13, 5))
eixos[0].plot([k for k, _ in resultados], [s for _, s in resultados], 'o-')
eixos[0].axvline(k_ideal, linestyle='--', color='red', label=f'Melhor K = {k_ideal}')
eixos[0].set(xlabel='Numero de grupos (K)', ylabel='Silhouette Score', title='Escolha do numero de grupos')
eixos[0].set_xticks([k for k, _ in resultados])
eixos[0].legend()

eixos[1].scatter(X[:, 0], X[:, 1], c=grupo, cmap='tab10', s=35)
eixos[1].scatter(centros[:, 0], centros[:, 1], c='black', marker='X', s=180, label='Centroides')
eixos[1].set(xlabel='Coordenada X', ylabel='Coordenada Y', title=f'Instancia {INSTANCE_ID}: {k_ideal} grupos')
eixos[1].legend()
plt.tight_layout()
plt.show()