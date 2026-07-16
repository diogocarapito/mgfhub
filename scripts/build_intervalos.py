"""Constrói data/intervalos_ide.csv em formato longo (uma linha por
indicador por ano) a partir das colunas por-ano do
data/sunburst_portaria_411a_2023.csv.

Um novo ano contratual passa a ser acrescentar linhas a este CSV — sem
alterações de código.

Executar a partir da raiz do repositório:
    python scripts/build_intervalos.py
"""

import pandas as pd

ANOS_DISPONIVEIS = (2023, 2024)


def build_intervalos():
    df = pd.read_csv("./data/sunburst_portaria_411a_2023.csv")

    # só indicadores (as linhas de dimensão não têm id nem intervalos próprios)
    df = df[df["id"].notna()]

    blocos = []
    for ano in ANOS_DISPONIVEIS:
        blocos.append(
            pd.DataFrame(
                {
                    "id": df["id"].astype(int),
                    "ano": ano,
                    "intervalo_esperado": df[f"Intervalo Esperado {ano}"],
                    "intervalo_aceitavel": df[f"Intervalo Aceitável {ano}"],
                    "min_aceitavel": df[f"Mínimo Aceitável {ano}"],
                    "max_aceitavel": df[f"Máximo Aceitável {ano}"],
                    "min_esperado": df[f"Mínimo Esperado {ano}"],
                    "max_esperado": df[f"Máximo Esperado {ano}"],
                }
            )
        )

    out = pd.concat(blocos, ignore_index=True).sort_values(["ano", "id"])
    out.to_csv("./data/intervalos_ide.csv", index=False)
    print(
        f"wrote data/intervalos_ide.csv ({out.shape[0]} linhas, anos {ANOS_DISPONIVEIS})"
    )


if __name__ == "__main__":
    build_intervalos()
