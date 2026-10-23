    if n < 2:
        raise ValueError("São necessários pelo menos 2 destinos para agrupar.")

    if k_fixo is not None:
        if not 1 <= k_fixo <= n:
            raise ValueError(f"K precisa estar entre 1 e {n}.")
        modelo = KMeans(n_clusters=k_fixo, random_state=42, n_init=10)
        grupos = modelo.fit_predict(X)
        score = silhouette_score(X, grupos) if 1 < k_fixo < n else None
        return modelo, [(k_fixo, score)]

    if n < 3:
        modelo = KMeans(n_clusters=1, random_state=42, n_init=10)
        modelo.fit(X)
        return modelo, [(1, None)]

    resultados = []
    modelos = {}
    for k in range(2, min(k_max, n - 1) + 1):
        modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
        grupos = modelo.fit_predict(X)
        if len(np.unique(grupos)) < 2 or len(np.unique(grupos)) >= n:
            continue
        score = silhouette_score(X, grupos)
        resultados.append((k, score))
        modelos[k] = modelo
        print(f"K={k:2d} | Silhouette Score={score:.4f}")

    if not resultados:
        raise ValueError("Não foi possível encontrar um agrupamento válido.")

    melhor_k, _ = max(resultados, key=lambda item: item[1])
    return modelos[melhor_k], resultados


def main():
    parser = argparse.ArgumentParser(
        description="Agrupa destinos por coordenadas usando K-Means."
    )
    parser.add_argument("--instance", type=int, default=0,
                        help="ID da instância do CSV (padrão: 0).")
    parser.add_argument("--k", type=int, default=None,
                        help="Número fixo de grupos. Se omitido, escolhe K pelo Silhouette Score.")
    parser.add_argument("--k-max", type=int, default=10,
                        help="Maior K testado na escolha automática (padrão: 10).")
    parser.add_argument("--csv", type=Path,
                        default=Path(__file__).with_name("tsp_dataset.csv"),
                        help="Caminho para tsp_dataset.csv.")
    parser.add_argument("--sem-grafico", action="store_true",
                        help="Não exibe gráficos.")
    args = parser.parse_args()

    X = carregar_instancia(args.csv, args.instance)
    modelo, resultados = escolher_k(X, args.k, args.k_max)
    grupos = modelo.labels_
    centros = modelo.cluster_centers_
    k_final = modelo.n_clusters

    scores_validos = [(k, s) for k, s in resultados if s is not None]
    melhor_score = next((s for k, s in scores_validos if k == k_final), None)

    print(f"\nInstância: {args.instance} | Destinos: {len(X)}")
    print(f"Número de grupos: {k_final}")
    if melhor_score is not None:
        print(f"Silhouette Score: {melhor_score:.4f}")

    for j in range(k_final):
        indices = np.where(grupos == j)[0]
        print(f"\nGrupo {j + 1}: {len(indices)} destinos")
        print("Destinos (índices começando em 0):", ", ".join(map(str, indices)))
        print(f"Centroide: X={centros[j][0]:.3f}, Y={centros[j][1]:.3f}")

    saida = Path(f"destinos_agrupados_instancia_{args.instance}.csv")
    with saida.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["instance_id", "destino_indice", "coordenada_x", "coordenada_y", "grupo"])
        for i, (coordenada, grupo) in enumerate(zip(X, grupos)):
            escritor.writerow([args.instance, i, coordenada[0], coordenada[1], int(grupo) + 1])
    print(f"\nArquivo de resultados salvo em: {saida.resolve()}")

    if not args.sem_grafico:
        fig, eixos = plt.subplots(1, 2, figsize=(13, 5))
        if scores_validos:
            ks = [k for k, _ in scores_validos]
            scores = [s for _, s in scores_validos]
            eixos[0].plot(ks, scores, "o-")
            eixos[0].set(xlabel="Número de grupos (K)", ylabel="Silhouette Score",
                         title="Escolha do número de grupos")
            eixos[0].set_xticks(ks)
            eixos[0].axvline(k_final, linestyle="--", label=f"K = {k_final}")
            eixos[0].legend()
        else:
            eixos[0].axis("off")
            eixos[0].text(0.5, 0.5, f"K fixo = {k_final}", ha="center", va="center")

        eixos[1].scatter(X[:, 0], X[:, 1], c=grupos, cmap="tab10", s=35)
        eixos[1].scatter(centros[:, 0], centros[:, 1], c="black", marker="X",
                         s=180, label="Centroides")
        eixos[1].set(xlabel="Coordenada X", ylabel="Coordenada Y",
                     title=f"Instância {args.instance}: {k_final} grupos")
        eixos[1].legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
