"""Gera coordenadas fictícias para testes a partir de um CSV de clientes."""
from pathlib import Path
import argparse
import random
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="dataset/database-improvisado.csv")
    parser.add_argument("--output", default="dataset/clientes-com-coordenadas.csv")
    args = parser.parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output

    if not input_path.is_file():
        raise FileNotFoundError(f"CSV de origem não encontrado: {input_path}")

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    random.seed(42)
    # Região aproximada usada apenas para dados de demonstração.
    df["latitude"] = [random.uniform(-25.334176, -25.332935) for _ in range(len(df))]
    df["longitude"] = [random.uniform(-49.411334, -49.397602) for _ in range(len(df))]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"CSV de teste gerado: {output_path} ({len(df)} registros)")


if __name__ == "__main__":
    main()
