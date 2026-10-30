# Rota-do-Oleo
Rota do Óleo, é um projeto em desenvolvimento na matéria de experiência criativa. Que busca criar um roteiro de visita a clientes.

Os arquivos estão estruturados em 
> funções, como o agrupador e o roteirizador
> Arquivos, as bases de datasets e os gerados pelo código

O algoritimo conta com uma base modificada e artificial com intuito de testar as possibilidades. Ele utiliza um randomizador de coordenadas, que está pre-configurado para gerar locais dentro da região metropolitana de Curitiba, podendo ser alterado conforme necessidade.

O Main.py ainda está sendo desenvolvido e permitirá rodar cada tarefa sem ter a necessidade de individualmente rodar cada arquivo. Como ainda não está pronto eis aqui o passo a passo:

Um arquivo csv com a lista com pelo menos as seguintes colunas:
(Ordem, Cliente)

Caso os arquivos não contenham as coordenadas e só se deseja testar, o algoritimo conta com um Dataset-creator que gerará uma coordenada aleatória dentro de um perimetro estipulado.

Primeiro, se roda o agrupador que visa criar grupos com um K-means, podendo alterar a quantidade de Ks desejados e salvando cada grupo em outro arquivo CSV, cada um conforme o cluster ilustrado.

Em sequência, se roda o Roteirizador KNN que fará uma rota partindo do ponto mais alto (podendo ser alterado para uma outra localização) e gerando uma rota CSV na pasta rotas com o nome do Cluster escolhido.