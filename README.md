# Rota do Óleo

Projeto em Python para agrupar clientes por proximidade geográfica e gerar uma rota aproximada de visita para cada grupo.

## Correções realizadas

- Caminhos de arquivos resolvidos a partir da raiz do projeto, não do diretório atual do terminal.
- O CSV padrão agora aponta para `dataset/clientes-com-coordenadas.csv`, que existe no repositório enviado.
- Leitura compatível com cabeçalhos que possuem espaços extras (`Cliente `, `Ordem `) e com `latitude`/`longitude`.
- Imports corrigidos para a estrutura real de pastas (`functions.agrupador` e `functions.roteirizador`).
- Importação de `yaml` adicionada e nome/capitalização de `Parameters.yaml` padronizados.
- Limite de clientes corrigido: a base fornecida contém 590 registros.
- K-Means permite escolher automaticamente o número de grupos pelo maior coeficiente silhouette (padrão: testar K de 2 a 10).
- Roteirização implementada como vizinho mais próximo com distância Haversine em quilômetros.
- Arquivos e gráficos de saída são gravados em pastas criadas automaticamente.
- Geocodificação é opcional; não é executada quando a base já possui coordenadas.

## Estrutura

```text
Rota-do-Oleo/
├── dataset/
│   └── clientes-com-coordenadas.csv
├── functions/
│   ├── main.py
│   ├── geocoding.py
│   ├── agrupador/
│   │   └── kmeans.py
│   └── roteirizador/
│       └── knn.py
├── output/
│   ├── grupos/
│   ├── rotas/
│   └── graficos/
├── Parameters.yaml
├── Requirements.txt
└── README.md
```

## Instalação (Windows / PowerShell)

Na raiz do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r Requirements.txt
```

## Execução

Execute sempre a partir da raiz do projeto:

```powershell
py -m functions.main
```

Não é necessário fazer `cd functions` nem executar `kmeans.py` diretamente. O comando acima executa o fluxo completo: leitura e validação do CSV, agrupamento, geração das rotas e criação dos gráficos.

## Arquivos gerados

- `output/grupos/clientes_agrupados.csv`: todos os clientes com a coluna `cluster`.
- `output/grupos/cluster_N.csv`: clientes de cada grupo.
- `output/grupos/centros_clusters.csv`: coordenadas dos centros dos grupos.
- `output/grupos/avaliacao_k.csv`: silhouette calculado para cada K testado.
- `output/rotas/rota_cluster_N.csv`: sequência de visitas para cada grupo.
- `output/graficos/rota_cluster_N.png`: gráfico da rota de cada grupo.
- `output/rota_do_oleo.log`: log da execução.

## Configurações importantes

Edite `Parameters.yaml`:

- `input.file`: caminho do CSV de entrada relativo à raiz.
- `clustering.auto_clusters`: `true` para selecionar K automaticamente; `false` para usar `n_clusters`.
- `clustering.min_clusters` e `clustering.max_clusters`: intervalo de K avaliado.
- `routing.start_point`: `highest_latitude` inicia pelo ponto mais ao norte; qualquer outro valor inicia pela primeira linha.
- `routing.return_to_start`: `true` adiciona o ponto inicial ao fim da rota.

## Observações

O silhouette é uma heurística para estimar a separação dos grupos, não uma garantia de que esse seja o número operacional ideal de equipes/rotas. O método do vizinho mais próximo gera uma rota aproximada e não garante a solução ótima do problema do caixeiro-viajante. Para uma rota real, também devem ser considerados trânsito, vias, restrições de circulação e horários de atendimento.

A geocodificação via Nominatim depende de internet e de uma coluna de endereços; mantenha-a desabilitada quando o CSV já possuir coordenadas. Respeite a política de uso do serviço.
