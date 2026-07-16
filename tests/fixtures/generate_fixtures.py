"""Gera os ficheiros xlsx sintéticos usados nos testes golden-master do ETL.

Os ficheiros imitam os formatos reais de exportação do BI-CSP e do MIM@UF
(incluindo as variantes com e sem cabeçalho de metadados) usando apenas
indicadores/intervalos reais da Portaria 411-A/2023. Nenhum dado real de
unidades ou médicos é usado.

Executar a partir da raiz do repositório:
    python tests/fixtures/generate_fixtures.py
"""

from pathlib import Path

from openpyxl import Workbook

FIXTURES_DIR = Path(__file__).resolve().parent


def _write(rows, filename):
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(FIXTURES_DIR / filename)
    print(f"wrote {filename}")


def bicsp_com_cabecalho():
    """BI-CSP com linha de filtros no topo (versão PT do export).

    Estrutura: linha 1 = filtros aplicados, linha 2 = lixo (descartada),
    linha 3 = cabeçalhos reais, linhas 4+ = dados.
    """
    headers = [
        "Cód. Indicador",
        "Designação Indicador (+ID)",
        "Hierarquia Contratual - Área",
        "Mês Ind",
        "Resultado",
        "Min. Aceit",
        "Máx. Aceit",
        " Min. Esper",  # espaço inicial existe no export real
        "Máx. Esper",
    ]
    hier = "IDE - Desempenho"
    data = [
        # (cód, designação, resultado, min_a, max_a, min_e, max_e)
        # esperados → score 2
        [
            "2013.008.01 FL",
            "Taxa utilização consultas PF (8)",
            75.0,
            38.0,
            100.0,
            60.0,
            100.0,
        ],
        # entre mínimo aceitável e mínimo esperado → score parcial
        [
            "2017.034.01 FL",
            "Prop. obesos c/ consulta (34)",
            60.0,
            55.0,
            100.0,
            72.0,
            100.0,
        ],
        # abaixo do mínimo aceitável → score 0
        [
            "2013.020.01 FL",
            "Prop. hipertensos < 65A (20)",
            30.0,
            45.0,
            100.0,
            67.0,
            100.0,
        ],
        # entre máximo esperado e máximo aceitável → score parcial
        [
            "2018.314.01 FL",
            "Prop. DM com PA >= 140/90 (314)",
            20.0,
            0.0,
            28.0,
            0.0,
            15.0,
        ],
        # acima do máximo aceitável → score 0
        [
            "2019.341.01 FL",
            "Despesa PVP medicamentos (341)",
            170.0,
            0.0,
            163.0,
            0.0,
            133.0,
        ],
        [
            "2019.365.01 FL",
            "Taxa internamentos evitáveis (365)",
            300.0,
            0.0,
            620.0,
            0.0,
            480.0,
        ],
        ["2020.412.01 FL", "Consultas dia UF (412)", 90.0, 40.0, 95.0, 60.0, 85.0],
        [
            "2013.095.01 FL",
            "Prop. jovens 14A c/ PNV (95)",
            96.5,
            90.0,
            100.0,
            95.0,
            100.0,
        ],
        # termina em FX mas é a exceção mantida pelo extrair_id
        [
            "2020.435.01 FX",
            "Vacinação gripe >= 65A (435)",
            64.0,
            62.0,
            100.0,
            66.0,
            100.0,
        ],
        # termina em FX → linha descartada pelo extrair_id
        [
            "2013.020.02 FX",
            "Duplicado FX a descartar (20)",
            999.0,
            45.0,
            100.0,
            67.0,
            100.0,
        ],
        # designação vazia → linha descartada
        ["2013.098.01 FL", None, 88.0, 80.0, 100.0, 93.0, 100.0],
    ]
    rows = [
        ["Filtros: Aplicados — Nome UF é USF Fixture"] + [None] * 8,
        ["(resumo)"] + [None] * 8,
        headers,
    ]
    for cod, desig, res, min_a, max_a, min_e, max_e in data:
        rows.append([cod, desig, hier, 202406, res, min_a, max_a, min_e, max_e])
    _write(rows, "bicsp_com_cabecalho_2024_06.xlsx")


def bicsp_sem_cabecalho():
    """BI-CSP sem linha de filtros (cabeçalhos na primeira linha).

    A unidade passa a ser o nome do ficheiro. Inclui uma linha IDG para
    exercitar o filtro de 'Hierarquia Contratual - Área'.
    """
    headers = [
        "Cód. Indicador",
        "Designação Indicador (+ID)",
        "Hierarquia Contratual - Área",
        "Mês Ind",
        "Resultado",
        "Min. Aceit",
        "Máx. Aceit",
        " Min. Esper",
        "Máx. Esper",
    ]
    rows = [headers]
    data = [
        [
            "2013.008.01 FL",
            "Taxa utilização consultas PF (8)",
            "IDE - Desempenho",
            202407,
            55.0,
            38.0,
            100.0,
            60.0,
            100.0,
        ],
        [
            "2017.039.01 FL",
            "Prop. DM c/ HbA1c (39)",
            "IDE - Desempenho",
            202407,
            80.0,
            50.0,
            100.0,
            70.0,
            100.0,
        ],
        [
            "2018.274.01 FL",
            "Prop. DM2 c/ insulina (274)",
            "IDE - Desempenho",
            202407,
            70.0,
            65.0,
            100.0,
            82.0,
            100.0,
        ],
        # linha IDG → excluída pelo filtro de hierarquia
        [
            "2013.023.01 FL",
            "Prop. hipertensos risco CV (23)",
            "IDG - Desempenho",
            202407,
            85.0,
            60.0,
            100.0,
            80.0,
            100.0,
        ],
    ]
    rows.extend(data)
    _write(rows, "bicsp_sem_cabecalho_2024_07.xlsx")


def mimuf_unidade():
    """MIM@UF exportado para a unidade inteira (10 colunas, sem metadados).

    A coluna 7 (0-based) tem o período no cabeçalho e o numerador nos dados.
    A primeira linha de dados é sempre descartada pelo ETL.
    """
    headers = [
        "Unidade Funcional / Polo Hospitalar",
        "Código",
        "Indicador",
        "Área",
        "Médico Familia",
        "Tipo",
        "Sexo",
        "2024-06",
        "Denominador",
        "Valor",
    ]
    unidade = "USF Fixture"
    # nomes com espaços duplos/finais para exercitar a normalização medico()
    ana = "ANA  PRIMEIRA "
    bruno = "BRUNO SEGUNDO"
    rows = [
        headers,
        # primeira linha de dados: sacrificial (descartada pelo ETL)
        [unidade, "x", "(totais)", "x", "x", "x", "x", "0", "0", "0"],
        # valores como strings em formato PT ("1.234,5") e como floats,
        # para exercitar os dois ramos da conversão
        [unidade, "c1", "2013.008.01 FL", "PF", ana, "t", "F", "302", "400", "75,5"],
        [unidade, "c1", "2017.034.01 FL", "Obes", ana, "t", "F", "60", "100", "60,0"],
        [
            unidade,
            "c1",
            "2013.020.01 FL",
            "HTA",
            ana,
            "t",
            "F",
            "1.230,0",
            "4.100,0",
            "30,0",
        ],
        [unidade, "c1", "2020.435.01 FL", "Vac", ana, "t", "F", "64", "100", "64,0"],
        [unidade, "c2", "2013.008.01 FL", "PF", bruno, "t", "M", "180", "400", 45.0],
        [unidade, "c2", "2017.034.01 FL", "Obes", bruno, "t", "M", "80", "100", "80,0"],
        [unidade, "c2", "2013.020.01 FL", "HTA", bruno, "t", "M", "70", "100", "70,0"],
        [unidade, "c2", "2020.435.01 FL", "Vac", bruno, "t", "M", "70", "100", "70,0"],
        # duplicado exato → removido pelo drop_duplicates
        [unidade, "c1", "2013.008.01 FL", "PF", ana, "t", "F", "302", "400", "75,5"],
        # sem id → removido pelo dropna
        [unidade, "c1", None, "PF", ana, "t", "F", "1", "2", "50,0"],
        # termina em FX → removido pelo extrair_id
        [unidade, "c1", "2019.999.01 FX", "PF", ana, "t", "F", "1", "2", "50,0"],
    ]
    _write(rows, "mimuf_unidade_2024_06.xlsx")


def mimuf_medico():
    """MIM@UF exportado por médico: bloco de metadados + tabela de 9 colunas.

    O ETL extrai o médico dos metadados e insere a coluna 'Médico Familia'.
    O cabeçalho tem uma célula vazia e um nome duplicado para exercitar o
    prepare_row_to_column. Mesma unidade/mês do mimuf_unidade para exercitar
    o ramo de concatenação (mesmo 'nome' no dicionário final).
    """
    rows = [
        ["P02.01.R03. Indicadores Contratualizados por Médico"] + [None] * 8,
        ["Unidade de Saúde: ULS Fixture"] + [None] * 8,
        ["Médico Familia: CARLA  TERCEIRA"] + [None] * 8,
        # cabeçalho real da tabela: célula vazia (→ NaN1) e "Área" duplicada (→ Área.1)
        [
            "Unidade Funcional / Polo Hospitalar",
            None,
            "Indicador",
            "Área",
            "Área",
            "Sexo",
            "2024-06",
            "Denominador",
            "Valor",
        ],
        # primeira linha de dados: sacrificial (fica sem médico e é descartada)
        ["USF Fixture", "x", "(cabeçalho repetido)", "x", "x", "x", "0", "0", "0"],
        ["USF Fixture", "c3", "2013.008.01 FL", "PF", "j", "F", "310", "400", "77,5"],
        ["USF Fixture", "c3", "2017.034.01 FL", "Obes", "j", "F", "58", "100", "58,0"],
        ["USF Fixture", "c3", "2018.314.01 FL", "DM", "j", "F", "18", "90", "20,0"],
        ["USF Fixture", "c3", "2019.341.01 FL", "Desp", "j", "F", "130", "1", "130,0"],
    ]
    _write(rows, "mimuf_medico_2024_06.xlsx")


if __name__ == "__main__":
    bicsp_com_cabecalho()
    bicsp_sem_cabecalho()
    mimuf_unidade()
    mimuf_medico()
