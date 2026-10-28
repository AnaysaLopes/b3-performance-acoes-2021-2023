"""Configurações do projeto: caminhos, período analisado e lista de ativos."""

from pathlib import Path

# Caminhos

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_BRONZE = RAIZ_PROJETO / "data" / "bronze"
PASTA_PRATA = RAIZ_PROJETO / "data" / "prata"
PASTA_OURO = RAIZ_PROJETO / "data" / "ouro"
PASTA_RELATORIOS = RAIZ_PROJETO / "docs" / "relatorios"

ARQ_BRONZE = PASTA_BRONZE / "cotacoes_brutas_yfinance.csv"

ARQ_PRATA = PASTA_PRATA / "cotacoes_tratadas.csv"

# Período analisado
DATA_INICIO = "2021-01-01"
DATA_FIM = "2023-12-31"
# data final exclusiva no yfinance
DATA_FIM_YFINANCE = "2024-01-01"

# Ativos analisados
# EMBR3 passou a ser negociada como EMBJ3 em 03/11/2025 e o Yahoo mantém o
# histórico apenas no código novo. O projeto usa EMBR3, código vigente no período.
ATIVOS = {
    "WEGE3":  {"empresa": "WEG",           "setor": "Bens Industriais",                "simbolo_yahoo": "WEGE3.SA"},
    "EMBR3":  {"empresa": "Embraer",       "setor": "Bens Industriais",                "simbolo_yahoo": "EMBJ3.SA"},
    "VALE3":  {"empresa": "Vale",          "setor": "Materiais Básicos",               "simbolo_yahoo": "VALE3.SA"},
    "GGBR4":  {"empresa": "Gerdau",        "setor": "Materiais Básicos",               "simbolo_yahoo": "GGBR4.SA"},
    "KLBN11": {"empresa": "Klabin",        "setor": "Materiais Básicos",               "simbolo_yahoo": "KLBN11.SA"},
    "PETR4":  {"empresa": "Petrobras",     "setor": "Petróleo, Gás e Biocombustíveis", "simbolo_yahoo": "PETR4.SA"},
    "PRIO3":  {"empresa": "PRIO",          "setor": "Petróleo, Gás e Biocombustíveis", "simbolo_yahoo": "PRIO3.SA"},
    "EGIE3":  {"empresa": "Engie Brasil",  "setor": "Utilidade Pública",               "simbolo_yahoo": "EGIE3.SA"},
    "ITUB4":  {"empresa": "Itaú Unibanco", "setor": "Financeiro",                      "simbolo_yahoo": "ITUB4.SA"},
    "BBDC4":  {"empresa": "Bradesco",      "setor": "Financeiro",                      "simbolo_yahoo": "BBDC4.SA"},
    "ABEV3":  {"empresa": "Ambev",         "setor": "Consumo não Cíclico",             "simbolo_yahoo": "ABEV3.SA"},
    "RENT3":  {"empresa": "Localiza",      "setor": "Consumo Cíclico",                 "simbolo_yahoo": "RENT3.SA"},
}


# Camada Ouro e parâmetros dos indicadores
ARQ_OURO_FATO = PASTA_OURO / "fato_cotacoes.csv"
ARQ_OURO_DIM = PASTA_OURO / "dim_ativos.csv"
ARQ_OURO_RESUMO = PASTA_OURO / "resumo_ativos_2021_2023.csv"

DIAS_UTEIS_ANO = 252
JANELA_SMA_CURTA = 21
JANELA_SMA_MEDIA = 50

# Paleta de cores por ativo (notebook e app)
CORES_ATIVOS = {
    "PETR4":  "#B39DDB",
    "PRIO3":  "#F48FB1",
    "EMBR3":  "#64B5F6",
    "WEGE3":  "#81C784",
    "VALE3":  "#FFB74D",
    "GGBR4":  "#4DB6AC",
    "KLBN11": "#FFD54F",
    "EGIE3":  "#FF8A65",
    "ITUB4":  "#7986CB",
    "BBDC4":  "#AED581",
    "ABEV3":  "#4DD0E1",
    "RENT3":  "#A1887F",
}
