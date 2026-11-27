# Rota do Óleo

Projeto desenvolvido em Python para automatizar o planejamento de rotas de atendimento de clientes, utilizando coordenadas geográficas, agrupamento por proximidade e algoritmos de roteirização.

O sistema recebe uma base de clientes, identifica grupos geograficamente próximos e gera uma sequência aproximada de visitas para cada grupo, facilitando a organização das equipes de atendimento.

---

## 1. Visão geral do funcionamento

A execução do projeto é centralizada no arquivo `functions/main.py`, responsável por coordenar todas as etapas do processamento.

O fluxo principal segue a seguinte sequência:

```text
                  INÍCIO
                     |
                     v
          Carregar Parameters.yaml
                     |
                     v
             Ler arquivo CSV
                     |
                     v
           Validar dados de entrada
                     |
                     v
          Coordenadas disponíveis?
                /         \
              NÃO          SIM
               |            |
               v            |
        Executar             |
        Geocodificação       |
               |            |
               +-----+------+
                     |
                     v
           Executar K-Means
                     |
                     v
          Definir quantidade de K
                     |
                     v
          Salvar grupos gerados
                     |
                     v
          Executar roteirização
                     |
                     v
          Gerar gráficos das rotas
                     |
                     v
             Registrar logs
                     |
                     v
                    FIM
```

Cada etapa possui uma responsabilidade específica e pode tomar decisões de acordo com os dados recebidos e as configurações definidas pelo usuário.

---

## 2. Fluxo de execução do Main

### 2.1. Inicialização e carregamento das configurações

O primeiro passo consiste em inicializar o sistema e carregar os parâmetros definidos no arquivo `Parameters.yaml`.

Esses parâmetros permitem modificar o comportamento do programa sem precisar alterar diretamente o código-fonte.

Entre as principais configurações estão:

- Caminho do arquivo CSV de entrada.
- Quantidade mínima e máxima de clusters.
- Seleção automática ou manual da quantidade de clusters.
- Critério para escolha do ponto inicial da rota.
- Definição sobre retornar ou não ao ponto inicial.

**Decisão tomada:** o programa utiliza os parâmetros externos para determinar como cada etapa será executada, mantendo as configurações separadas da implementação dos algoritmos.

### 2.2. Leitura e validação dos dados

Após carregar as configurações, o sistema realiza a leitura do arquivo CSV informado em `input.file`.

A base deve conter os dados dos clientes e suas respectivas coordenadas geográficas.

As informações utilizadas no processamento incluem:

| Campo | Descrição |
|---|---|
| Cliente | Identificação do estabelecimento |
| Ordem | Identificação ou ordem original do cliente |
| Latitude | Coordenada geográfica de latitude |
| Longitude | Coordenada geográfica de longitude |

O programa também considera possíveis inconsistências nos cabeçalhos, como espaços extras, e padroniza a utilização das colunas.

**Decisão tomada:** caso a base já possua latitude e longitude, o sistema aproveita essas informações. Caso contrário, poderá utilizar a etapa de geocodificação, desde que exista uma coluna de endereços disponível.

### 2.3. Geocodificação dos clientes

A geocodificação é uma etapa condicional do processamento.

Quando os clientes não possuem coordenadas geográficas, o módulo `geocoding.py` pode utilizar o serviço Nominatim para transformar endereços em coordenadas.

O resultado permite que os clientes sejam representados geograficamente e utilizados pelos algoritmos seguintes.

**Decisão tomada:**

- Se as coordenadas já existem, a geocodificação é ignorada.
- Se as coordenadas não existem e há endereços disponíveis, a geocodificação pode ser executada.
- Se não houver informações suficientes para obter as coordenadas, não será possível realizar o agrupamento geográfico corretamente.

Essa decisão evita consultas desnecessárias à API quando a base já está preparada.

### 2.4. Agrupamento geográfico com K-Means

Com os dados preparados, o sistema executa o módulo `functions/agrupador/kmeans.py`.

O objetivo dessa etapa é dividir os clientes em grupos geograficamente próximos, reduzindo a dispersão dos destinos que serão atendidos por cada equipe.

O algoritmo K-Means utiliza as coordenadas de latitude e longitude para encontrar agrupamentos.

**Decisão sobre a quantidade de clusters:**

O sistema oferece duas possibilidades:

**Modo automático (`auto_clusters: true`)**

O programa testa diferentes quantidades de clusters, considerando o intervalo definido por `min_clusters` e `max_clusters`.

Para cada quantidade de grupos, calcula o coeficiente Silhouette e utiliza o melhor resultado encontrado para selecionar o número de clusters.

**Modo manual (`auto_clusters: false`)**

O programa utiliza diretamente a quantidade de grupos definida em `n_clusters`.

**Por que essa decisão?**

A seleção automática permite estimar uma divisão geográfica adequada sem exigir que o usuário conheça previamente a quantidade ideal de grupos. Já o modo manual permite controlar diretamente a quantidade de equipes ou rotas desejadas.

Após o agrupamento, são gerados:

- `clientes_agrupados.csv`: base completa com a identificação do cluster de cada cliente.
- `cluster_N.csv`: arquivo individual contendo os clientes de cada grupo.
- `centros_clusters.csv`: coordenadas dos centros dos grupos.
- `avaliacao_k.csv`: resultados do coeficiente Silhouette para cada quantidade de clusters testada.

### 2.5. Roteirização dos grupos com KNN

Após a criação dos grupos, o sistema executa o módulo `functions/roteirizador/knn.py`.

Cada cluster é processado individualmente para determinar uma sequência de visitas.

O método utilizado é o **vizinho mais próximo (Nearest Neighbor)**, que busca construir uma rota selecionando, a cada passo, o cliente mais próximo da localização atual.

Para calcular as distâncias entre os pontos, é utilizada a fórmula de Haversine, que considera a curvatura da Terra e retorna distâncias aproximadas em quilômetros.

**Decisões tomadas durante a roteirização:**

1. Definição do ponto inicial:
   - `highest_latitude`: inicia pelo cliente mais ao norte do grupo.
   - Outro valor: inicia pelo primeiro cliente da base.

2. Seleção do próximo destino:
   - O algoritmo calcula as distâncias entre o ponto atual e os clientes ainda não visitados.
   - Seleciona o cliente com a menor distância.
   - Repete o processo até que todos os clientes tenham sido visitados.

3. Retorno ao ponto inicial:
   - Se `return_to_start` estiver habilitado, o ponto inicial é adicionado novamente ao final da sequência.
   - Caso contrário, a rota termina no último cliente visitado.

Cada grupo recebe uma rota independente, armazenada em `output/rotas/rota_cluster_N.csv`.

**Por que utilizar esse método?**

O vizinho mais próximo é uma abordagem simples e computacionalmente eficiente para construir rotas aproximadas. Entretanto, não garante a menor distância total possível.

### 2.6. Geração dos gráficos

Depois da roteirização, o sistema gera representações gráficas das rotas calculadas.

Cada gráfico apresenta a sequência de atendimento dos clientes de um cluster, permitindo visualizar a distribuição geográfica dos destinos e a ordem de visita.

Os gráficos são armazenados em:

`output/graficos/rota_cluster_N.png`

Essa etapa permite verificar visualmente os resultados e identificar possíveis problemas na distribuição dos clientes ou na sequência de visitas.

### 2.7. Registro da execução

Durante o processamento, o sistema utiliza registros de log para documentar a execução.

O arquivo `output/rota_do_oleo.log` permite acompanhar informações sobre o processamento e auxiliar na identificação de erros.

Os logs também facilitam a manutenção e o diagnóstico de problemas sem a necessidade de acompanhar diretamente todas as operações do código.

---

## 3. Estrutura do projeto

```text
Rota-do-Oleo/
│
├── dataset/
│   └── clientes-com-coordenadas.csv
│
├── functions/
│   ├── main.py
│   ├── geocoding.py
│   │
│   ├── agrupador/
│   │   └── kmeans.py
│   │
│   └── roteirizador/
│       └── knn.py
│
├── output/
│   ├── grupos/
│   ├── rotas/
│   ├── graficos/
│   └── rota_do_oleo.log
│
├── Parameters.yaml
├── Requirements.txt
└── README.md
```

### Responsabilidade dos módulos

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Coordenar o fluxo completo do sistema |
| `geocoding.py` | Converter endereços em coordenadas |
| `agrupador/kmeans.py` | Agrupar clientes por proximidade |
| `roteirizador/knn.py` | Definir a sequência de visitas |
| `Parameters.yaml` | Centralizar as configurações |
| `Requirements.txt` | Listar as dependências Python |

---

## 4. Instalação

Requisitos: Python instalado e acesso ao terminal PowerShell.

Na raiz do projeto, execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r Requirements.txt
```

---

## 5. Execução

O projeto deve ser executado a partir da raiz do repositório:

```powershell
py -m functions.main
```

Não é necessário entrar na pasta `functions` nem executar os módulos individualmente.

O `main.py` é responsável por coordenar as etapas de leitura, preparação dos dados, agrupamento, roteirização e geração dos resultados.

---

## 6. Arquivos de saída

Ao final da execução, os resultados são organizados automaticamente nas seguintes pastas:

| Arquivo | Conteúdo |
|---|---|
| `grupos/clientes_agrupados.csv` | Todos os clientes identificados por cluster |
| `grupos/cluster_N.csv` | Clientes pertencentes a cada grupo |
| `grupos/centros_clusters.csv` | Centros geográficos dos clusters |
| `grupos/avaliacao_k.csv` | Avaliação Silhouette das quantidades de grupos testadas |
| `rotas/rota_cluster_N.csv` | Sequência de visitas de cada grupo |
| `graficos/rota_cluster_N.png` | Representação gráfica de cada rota |
| `rota_do_oleo.log` | Registro da execução |

---

## 7. Configurações do sistema

As principais configurações podem ser modificadas no arquivo `Parameters.yaml`.

| Parâmetro | Função |
|---|---|
| `input.file` | Define o CSV de entrada |
| `clustering.auto_clusters` | Ativa ou desativa a escolha automática de K |
| `clustering.min_clusters` | Quantidade mínima de clusters testados |
| `clustering.max_clusters` | Quantidade máxima de clusters testados |
| `clustering.n_clusters` | Quantidade de clusters no modo manual |
| `routing.start_point` | Define o critério de escolha do ponto inicial |
| `routing.return_to_start` | Define se a rota retorna ao ponto inicial |

---

## 8. Limitações e considerações

É importante considerar algumas limitações dos métodos utilizados:

- **K-Means:** utiliza proximidade geográfica para agrupar clientes, mas não considera diretamente o trânsito, as condições das vias ou os horários de atendimento.
- **Silhouette:** é uma métrica heurística para avaliar a separação dos grupos, não garantindo que a quantidade selecionada seja operacionalmente ideal.
- **Vizinho mais próximo:** produz uma rota aproximada, mas não garante a menor distância total.
- **Haversine:** calcula distâncias geográficas em linha reta, não a distância real percorrida pelas ruas.
- **Nominatim:** depende de conexão com a internet e deve ser utilizado respeitando sua política de uso.

Portanto, os resultados devem ser considerados uma aproximação para o planejamento logístico, podendo ser aprimorados futuramente com informações de malha viária, trânsito e restrições de atendimento.

---

## 9. Possíveis evoluções

O projeto pode ser expandido futuramente com:

- Integração com APIs de roteamento viário.
- Consideração de horários de atendimento dos clientes.
- Balanceamento da quantidade de clientes entre equipes.
- Otimização das rotas considerando distância total.
- Inclusão de restrições de capacidade dos veículos.
