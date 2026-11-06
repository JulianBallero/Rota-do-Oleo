# Rota do Óleo
Rota do Óleo, é um projeto em desenvolvimento na matéria de experiência criativa. Que com base em uma lista de clientes, busca criar e armazenar um roteiro de visitas.

## Requeriments
Para instalar as Bibliotecas necessárias para rodar o código, rode no terminal:
pip install -r requirements.txt

## Estrutura
Os arquivos estão estruturados em 
> funções, como o agrupador e o roteirizador, etc.
> Arquivos, as bases de datasets e os gerados pelo código no Output
> a função Main
> arquivos ReadME, requerimentos e parametros

Rota-do-Oleo/
│
├── dataset/
│   └── clientes.csv
│
├── output/
│   ├── grupos/
│   ├── rotas/
│   ├── graficos/
│   └── rota_do_oleo.log
│
├── functions/
│   ├── main.py
│   ├── kmeans.py
│   ├── knn.py
│   └── geocoding.py
│
├── parameters.yaml
├── requirements.txt
└── README.md

## Como rodar:
