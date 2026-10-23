import pandas as pd

# Ler o arquivo CSV
df = pd.read_csv("visitas.csv", sep=",", encoding="utf-8")

# Classificar cada intervalo de horário
def classificar_horario(horario):
    inicio, fim = horario.split("-")

    inicio = pd.to_datetime(inicio.strip(), format="%H:%M").time()
    fim = pd.to_datetime(fim.strip(), format="%H:%M").time()
    meio_dia = pd.to_datetime("12:00", format="%H:%M").time()

    if fim <= meio_dia:
        return "Manhã"
    elif inicio >= meio_dia:
        return "Tarde"
    else:
        return "Ambos"

# Criar a coluna de classificação
df["classificacao"] = df["horario de visitas"].apply(
    classificar_horario
)

# Salvar o resultado em outro CSV
df.to_csv("visitas_classificadas.csv", index=False, encoding="utf-8-sig")

# Exibir o resultado
print(df)
