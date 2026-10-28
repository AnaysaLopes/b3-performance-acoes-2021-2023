"""
Limpeza e padronização da base (camada Prata).
Registros atípicos são sinalizados nas colunas fg_, sem exclusão nem preenchimento.

Uso: python -m src.tratamento
"""

import pandas as pd

from src import config

LIMITE_VARIACAO_EXTREMA = 0.15

NOMES_COLUNAS = {
    "Date": "dt_pregao",
    "ticker": "cd_ticker",
    "simbolo_yahoo": "cd_simbolo_yahoo",
    "Open": "vl_abertura",
    "High": "vl_maxima",
    "Low": "vl_minima",
    "Close": "vl_fechamento",
    "Adj Close": "vl_fechamento_ajustado",
    "Volume": "qt_volume_acoes",
    "Dividends": "vl_dividendos",
    "Stock Splits": "vl_fator_desdobramento",
    "data_extracao": "dt_extracao",
}
COLUNAS_PRECO = ["vl_abertura", "vl_maxima", "vl_minima", "vl_fechamento", "vl_fechamento_ajustado"]

relatorio = []


def registrar(texto=""):
    print(texto)
    relatorio.append(str(texto))


def titulo(texto):
    registrar()
    registrar("=" * 70)
    registrar(texto)
    registrar("=" * 70)


def tratar(df):
    linhas_bronze = len(df)
    titulo("0. ENTRADA · camada Bronze")
    registrar(f"Linhas lidas: {linhas_bronze}")
    registrar(f"Colunas: {df.columns.tolist()}")

    titulo("1. ENCODING E CAMPOS DE TEXTO")
    registrar("Arquivo lido e gravado em UTF-8.")
    corrompidos = 0
    for col in ["ticker", "simbolo_yahoo"]:
        corrompidos += int(df[col].astype(str).str.contains("Ã|Â|�").sum())
        df[col] = df[col].astype(str).str.strip().str.upper()
    registrar(f"Valores de texto com caracteres corrompidos: {corrompidos}")
    registrar("Campos de texto padronizados: sem espaços nas pontas e em caixa alta.")

    titulo("2. PADRONIZAÇÃO DOS NOMES DE COLUNAS")
    df = df.rename(columns=NOMES_COLUNAS)
    for antigo, novo in NOMES_COLUNAS.items():
        registrar(f"{antigo:<15} -> {novo}")

    titulo("3. PADRONIZAÇÃO DE DATAS")
    exemplo_antes = df["dt_pregao"].iloc[0]
    datas = pd.to_datetime(df["dt_pregao"], utc=True, errors="coerce")
    registrar(f"Datas que não puderam ser convertidas: {int(datas.isna().sum())}")
    df["dt_pregao"] = datas.dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None).dt.normalize()
    df["dt_extracao"] = pd.to_datetime(df["dt_extracao"])
    registrar(f"Exemplo antes:  {exemplo_antes}")
    registrar(f"Exemplo depois: {df['dt_pregao'].iloc[0].date()}")

    titulo("4. CONFERÊNCIA DO PERÍODO ANALISADO")
    fora = ~df["dt_pregao"].between(config.DATA_INICIO, config.DATA_FIM)
    registrar(f"Período analisado: {config.DATA_INICIO} a {config.DATA_FIM}")
    registrar(f"Primeiro pregão: {df['dt_pregao'].min().date()} | Último pregão: {df['dt_pregao'].max().date()}")
    registrar(f"Linhas fora do período: {int(fora.sum())}")
    df = df[~fora].copy()

    titulo("5. CONVERSÃO DE TIPOS NUMÉRICOS")
    for col in COLUNAS_PRECO + ["qt_volume_acoes", "vl_dividendos", "vl_fator_desdobramento"]:
        antes = int(df[col].isna().sum())
        df[col] = pd.to_numeric(df[col], errors="coerce")
        registrar(f"{col:<25} valores não numéricos encontrados: {int(df[col].isna().sum()) - antes}")
    df["qt_volume_acoes"] = df["qt_volume_acoes"].astype("Int64")

    titulo("6. VALORES NULOS")
    for col, qtd in df.isna().sum().items():
        registrar(f"{col:<25} {qtd}")
    sem_preco = df["vl_fechamento_ajustado"].isna()
    registrar(f"Linhas sem fechamento ajustado (inutilizáveis nos cálculos): {int(sem_preco.sum())}")
    registrar("Decisão: nenhum valor é preenchido artificialmente (sem média nem repetição).")
    df = df[~sem_preco].copy()

    titulo("7. DUPLICADOS")
    dup = df.duplicated(subset=["cd_ticker", "dt_pregao"])
    registrar(f"Repetições da chave ativo + data: {int(dup.sum())}")
    df = df[~dup].copy()

    titulo("8. PREÇOS MENORES OU IGUAIS A ZERO")
    invalido = (df[COLUNAS_PRECO] <= 0).any(axis=1)
    registrar(f"Linhas com algum preço <= 0: {int(invalido.sum())}")
    df = df[~invalido].copy()

    titulo("9. CONSISTÊNCIA ENTRE MÁXIMA, MÍNIMA, ABERTURA E FECHAMENTO")
    incoerente = (
        (df["vl_maxima"] < df[["vl_abertura", "vl_fechamento"]].max(axis=1) - 1e-6)
        | (df["vl_minima"] > df[["vl_abertura", "vl_fechamento"]].min(axis=1) + 1e-6)
    )
    registrar(f"Linhas incoerentes: {int(incoerente.sum())}")

    titulo("10. SINALIZAÇÕES (os dados são mantidos, só marcados)")
    df = df.sort_values(["cd_ticker", "dt_pregao"]).reset_index(drop=True)

    df["fg_volume_zero"] = (df["qt_volume_acoes"] == 0).astype(int)
    registrar(f"fg_volume_zero = 1 em {int(df['fg_volume_zero'].sum())} linhas:")
    registrar(df.loc[df["fg_volume_zero"] == 1,
                     ["cd_ticker", "dt_pregao", "vl_abertura", "vl_maxima", "vl_minima", "vl_fechamento"]
                     ].to_string(index=False))
    registrar("Leitura: são ações líquidas, as demais negociaram normalmente nesses dias e os")
    registrar("quatro preços repetem o fechamento anterior. Indício de falha de registro na fonte.")
    registrar("Decisão: manter (preservar o dado real) e documentar como limitação.")

    variacao = df.groupby("cd_ticker")["vl_fechamento_ajustado"].pct_change(fill_method=None)
    df["fg_variacao_extrema"] = (variacao.abs() > LIMITE_VARIACAO_EXTREMA).astype(int)
    extremos = df.loc[df["fg_variacao_extrema"] == 1, ["cd_ticker", "dt_pregao"]].copy()
    extremos["variacao_%"] = (variacao[df["fg_variacao_extrema"] == 1] * 100).round(2)
    registrar(f"\nfg_variacao_extrema = 1 (|variação diária| > {LIMITE_VARIACAO_EXTREMA:.0%}) em {len(extremos)} linhas:")
    registrar(extremos.to_string(index=False))
    registrar("Decisão: manter. Movimentos fortes fazem parte do risco que o projeto mede (P3 e P4).")

    titulo("11. COLUNAS DERIVADAS")
    df["nm_empresa"] = df["cd_ticker"].map(lambda t: config.ATIVOS[t]["empresa"])
    df["ds_setor"] = df["cd_ticker"].map(lambda t: config.ATIVOS[t]["setor"])
    df["vl_volume_financeiro"] = df["vl_fechamento"] * df["qt_volume_acoes"]
    registrar("nm_empresa e ds_setor: a partir de src/config.py")
    registrar("vl_volume_financeiro = vl_fechamento x qt_volume_acoes (estimativa em R$)")

    ordem = ["dt_pregao", "cd_ticker", "nm_empresa", "ds_setor"] + COLUNAS_PRECO + [
        "qt_volume_acoes", "vl_volume_financeiro", "vl_dividendos", "vl_fator_desdobramento",
        "fg_volume_zero", "fg_variacao_extrema", "cd_simbolo_yahoo", "dt_extracao",
    ]
    df = df[ordem]

    titulo("12. VALIDAÇÃO FINAL")
    resumo = df.groupby("cd_ticker").agg(
        pregoes=("dt_pregao", "count"),
        primeiro=("dt_pregao", "min"),
        ultimo=("dt_pregao", "max"),
        setor=("ds_setor", "first"),
    )
    resumo["primeiro"] = resumo["primeiro"].dt.date
    resumo["ultimo"] = resumo["ultimo"].dt.date
    registrar(resumo.to_string())
    registrar(f"\nLinhas na Bronze: {linhas_bronze} | Linhas na Prata: {len(df)} | Perda: {linhas_bronze - len(df)}")
    registrar("\nTipos finais:")
    registrar(df.dtypes.to_string())
    return df


def main():
    df_bronze = pd.read_csv(config.ARQ_BRONZE, encoding="utf-8")

    registrar("RELATÓRIO DE TRATAMENTO · CAMADA PRATA")
    registrar("Projeto Final · Performance de Ações da B3 (2021 a 2023)")
    df_prata = tratar(df_bronze)

    config.PASTA_PRATA.mkdir(parents=True, exist_ok=True)
    df_prata.to_csv(config.ARQ_PRATA, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    registrar(f"\nArquivo gravado: {config.ARQ_PRATA.relative_to(config.RAIZ_PROJETO)}")

    config.PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
    caminho = config.PASTA_RELATORIOS / "relatorio_tratamento.txt"
    caminho.write_text("\n".join(relatorio) + "\n", encoding="utf-8")
    print(f"Relatório gravado: {caminho.relative_to(config.RAIZ_PROJETO)}")


if __name__ == "__main__":
    main()