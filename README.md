# 🛢️ Rota do Óleo

Projeto desenvolvido na disciplina de **Experiência Criativa**. A partir de uma lista de clientes, o sistema **agrupa os clientes por proximidade geográfica, define a ordem de visita em cada grupo e armazena os roteiros gerados**.

## Fluxo do projeto

```
clientes.csv → Geocodificação → Agrupamento (K-Means) → Roteirização (KNN) → Saídas
```

| Etapa | Arquivo | Entrada | Saída |
|---|---|---|---|
| 1. Geocodificação | `geocoding.py` | Endereços do `clientes.csv` | Latitude e longitude de cada cliente |
| 2. Agrupamento | `kmeans.py` | Coordenadas dos clientes | Grupos de clientes próximos entre si |
| 3. Roteirização | `knn.py` | Clientes de cada grupo | Ordem de visita por grupo |
| 4. Saídas | `main.py` | Resultados das etapas anteriores | Arquivos em `output/` |

## Decisões por etapa

### 1. Geocodificação
- **O que faz:** converte o endereço de cada cliente em coordenadas geográficas.
- **Por que:** os algoritmos de agrupamento e rota trabalham com distâncias, então precisam de números, não de texto.
- **Decisão:** `[CONFIRMAR: qual serviço/biblioteca é usado, ex.: Nominatim/geopy, e por quê]`
- **Alternativas consideradas:** `[CONFIRMAR: ex.: Google Maps API (paga), coordenadas já presentes no CSV]`
- **Trade-off:** `[CONFIRMAR: ex.: serviço gratuito tem limite de requisições e pode falhar em endereços incompletos]`

### 2. Agrupamento com K-Means
- **O que faz:** divide os clientes em *k* grupos, cada um com clientes geograficamente próximos.
- **Por que:** visitar todos os clientes em uma única rota é inviável. Dividir em grupos permite distribuir o trabalho em dias ou veículos diferentes.
- **Decisão:** K-Means pela simplicidade e porque agrupa naturalmente por distância entre pontos. O número de grupos é definido em `parameters.yaml`.
- **Alternativas consideradas:** `[CONFIRMAR: ex.: DBSCAN, clusterização hierárquica]`
- **Trade-off:** o K-Means exige definir *k* antecipadamente e não garante grupos com o mesmo tamanho.

### 3. Roteirização com KNN
- **O que faz:** dentro de cada grupo, define a sequência de visitas a partir do vizinho mais próximo.
- **Por que:** é uma heurística simples e rápida para ordenar visitas sem resolver o problema completo do caixeiro viajante.
- **Decisão:** `[CONFIRMAR: ponto de partida da rota (depósito? primeiro cliente?) e métrica de distância (euclidiana, haversine)]`
- **Alternativas consideradas:** `[CONFIRMAR: ex.: otimização exata, OR-Tools]`
- **Trade-off:** a rota gerada é boa, mas não necessariamente a ótima.

### 4. Armazenamento e saídas
- **O que faz:** salva os resultados em `output/` para consulta posterior.
- **Por que:** manter os roteiros armazenados permite reutilizá-los e auditar o que foi gerado.
- **Log:** `rota_do_oleo.log` registra cada execução, facilitando a identificação de erros (ex.: endereço não localizado).

## Estrutura do projeto

```
Rota-do-Oleo/
│
├── dataset/
│   └── clientes.csv            # Base de clientes (entrada)
│
├── output/                     # Gerado pelo código
│   ├── grupos/                 # Clientes por grupo
│   ├── rotas/                  # Ordem de visita por grupo
│   ├── graficos/               # Visualizações dos grupos e rotas
│   └── rota_do_oleo.log        # Registro da execução
│
├── functions/
│   ├── main.py                 # Orquestra todo o fluxo
│   ├── geocoding.py            # Etapa 1
│   ├── kmeans.py               # Etapa 2
│   └── knn.py                  # Etapa 3
│
├── parameters.yaml             # Parâmetros (ex.: número de grupos)
├── requirements.txt            # Dependências
└── README.md
```

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Confira os parâmetros em `parameters.yaml` `[CONFIRMAR: quais parâmetros existem]`.
3. Coloque sua lista de clientes em `dataset/clientes.csv` `[CONFIRMAR: colunas esperadas]`.
4. Execute:
   ```bash
   python functions/main.py
   ```
5. Os resultados serão gerados na pasta `output/`.