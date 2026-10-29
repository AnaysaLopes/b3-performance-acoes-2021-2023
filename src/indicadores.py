"""
Cálculo dos indicadores financeiros (camada Ouro).
As funções também são usadas no notebook e no app.

Uso: python -m src.indicadores
"""

import numpy as np
import pandas as pd

from src import config

PRECO = "vl_fechamento_ajustado"


# Indicadores diários
def retorno_diario(df):
    """Variação do preço em relação ao pregão anterior (0.02 = +2%)."""
    return df.groupby("cd_ticker")[PRECO].pct_change(fill_method=None)


def media_movel(df, janela):
    """Média simples dos últimos 'janela' fechamentos."""
    return df.groupby("cd_ticker")[PRECO].transform(
        lambda serie: serie.rolling(window=janela, min_periods=janela).mean()
    )


def base_100(df):
    """Preço normalizado: o primeiro pregão de cada ativo vale 100."""
    return df.groupby("cd_ticker")[PRECO].transform(lambda serie: serie / serie.iloc[0] * 100)


def drawdown(df):
    """Queda em relação ao maior preço já atingido (-0.30 = 30% abaixo do topo)."""
    return df.groupby("cd_ticker")[PRECO].transform(lambda serie: serie / serie.cummax() - 1)


def preparar_recorte(df):
    """
    Recalcula os indicadores que dependem do ponto de partida do período.
    As médias móveis não são recalculadas: vêm prontas da camada Ouro.
    """
    recorte = df.sort_values(["cd_ticker", "dt_pregao"]).copy()
    recorte["vl_retorno_periodo"] = retorno_diario(recorte)
    recorte["vl_base_100"] = base_100(recorte)
    recorte["vl_drawdown"] = drawdown(recorte)
    return recorte


# Resumo por ativo
def resumo_por_ativo(df):
    recorte = preparar_recorte(df)
    linhas = []

    for ticker, g in recorte.groupby("cd_ticker"):
        precos = g[PRECO]
        retornos = g["vl_retorno_periodo"].dropna()
        if len(retornos) < 2:
            continue

        retorno_acumulado = precos.iloc[-1] / precos.iloc[0] - 1
        retorno_anualizado = (1 + retorno_acumulado) ** (config.DIAS_UTEIS_ANO / len(retornos)) - 1
        volatilidade = retornos.std() * np.sqrt(config.DIAS_UTEIS_ANO)
        sharpe = retorno_anualizado / volatilidade if volatilidade > 0 else np.nan

        idx_vale = g["vl_drawdown"].idxmin()
        idx_topo = g.loc[:idx_vale, PRECO].idxmax()

        com_sma = g.dropna(subset=["vl_sma_50"])
        pct_acima_sma50 = (com_sma[PRECO] > com_sma["vl_sma_50"]).mean() if len(com_sma) else np.nan
        ambas = g.dropna(subset=["vl_sma_21", "vl_sma_50"])
        lado = np.sign(ambas["vl_sma_21"] - ambas["vl_sma_50"])
        cruzamentos = int((lado.diff().fillna(0) != 0).sum())

        linhas.append({
            "cd_ticker": ticker,
            "nm_empresa": g["nm_empresa"].iloc[0],
            "ds_setor": g["ds_setor"].iloc[0],
            "dt_inicio": g["dt_pregao"].iloc[0],
            "dt_fim": g["dt_pregao"].iloc[-1],
            "qt_pregoes": len(g),
            "vl_preco_inicial": precos.iloc[0],
            "vl_preco_final": precos.iloc[-1],
            "vl_base_100_final": precos.iloc[-1] / precos.iloc[0] * 100,
            "vl_retorno_acumulado": retorno_acumulado,
            "vl_retorno_anualizado": retorno_anualizado,
            "vl_volatilidade_anualizada": volatilidade,
            "vl_indice_sharpe_empirico": sharpe,
            "vl_drawdown_maximo": g["vl_drawdown"].min(),
            "dt_topo_antes_drawdown": g.loc[idx_topo, "dt_pregao"],
            "dt_vale_drawdown": g.loc[idx_vale, "dt_pregao"],
            "vl_retorno_diario_medio": retornos.mean(),
            "vl_retorno_diario_desvio": retornos.std(),
            "vl_retorno_diario_min": retornos.min(),
            "vl_retorno_diario_max": retornos.max(),
            "vl_assimetria": retornos.skew(),
            "vl_curtose": retornos.kurt(),
            "vl_volume_financeiro_medio": g["vl_volume_financeiro"].mean(),
            "pc_pregoes_acima_sma50": pct_acima_sma50,
            "qt_cruzamentos_sma21_sma50": cruzamentos,
        })

    return pd.DataFrame(linhas)


def kpis_carteira(resumo):
    """
    KPIs estratégicos da carteira. O retorno médio da carteira considera o
    mesmo valor aplicado em cada ativo no primeiro pregão, sem rebalanceamento.
    """
    melhor = resumo.loc[resumo["vl_retorno_acumulado"].idxmax()]
    pior = resumo.loc[resumo["vl_retorno_acumulado"].idxmin()]
    return {
        "retorno_medio_carteira": resumo["vl_retorno_acumulado"].mean(),
        "ativo_destaque": melhor["cd_ticker"],
        "retorno_ativo_destaque": melhor["vl_retorno_acumulado"],
        "ativo_menor_performance": pior["cd_ticker"],
        "retorno_ativo_menor_performance": pior["vl_retorno_acumulado"],
        "volatilidade_media": resumo["vl_volatilidade_anualizada"].mean(),
    }


def matriz_correlacao(df):
    """Correlação de Pearson entre os retornos diários dos ativos."""
    recorte = preparar_recorte(df)
    tabela = recorte.pivot(index="dt_pregao", columns="cd_ticker", values="vl_retorno_periodo")
    return tabela.corr(method="pearson")


# Camada Ouro
def gerar_camada_ouro(prata):
    df = prata.sort_values(["cd_ticker", "dt_pregao"]).reset_index(drop=True)
    df["vl_retorno_diario"] = retorno_diario(df)
    df["vl_sma_21"] = media_movel(df, config.JANELA_SMA_CURTA)
    df["vl_sma_50"] = media_movel(df, config.JANELA_SMA_MEDIA)

    fato = df[[
        "dt_pregao", "cd_ticker",
        "vl_abertura", "vl_maxima", "vl_minima", "vl_fechamento", "vl_fechamento_ajustado",
        "qt_volume_acoes", "vl_volume_financeiro",
        "vl_retorno_diario", "vl_sma_21", "vl_sma_50",
        "fg_volume_zero", "fg_variacao_extrema",
    ]]
    dim = (
        df[["cd_ticker", "nm_empresa", "ds_setor", "cd_simbolo_yahoo"]]
        .drop_duplicates("cd_ticker")
        .reset_index(drop=True)
    )
    return fato, dim


def juntar_fato_dim(fato, dim):
    return fato.merge(dim, on="cd_ticker", how="left")


# Relatório
def pct(x, casas=1):
    return f"{x * 100:.{casas}f}%".replace(".", ",")


def num(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def gerar_relatorio(base, resumo):
    L = []
    def linha(t=""):
        L.append(t)
    def titulo(t):
        linha(); linha("=" * 70); linha(t); linha("=" * 70)

    linha("RELATÓRIO DE INDICADORES · CAMADA OURO")
    linha(f"Período: {base['dt_pregao'].min().date()} a {base['dt_pregao'].max().date()} · {base['cd_ticker'].nunique()} ativos")

    k = kpis_carteira(resumo)
    titulo("KPIs ESTRATÉGICOS")
    linha(f"Retorno médio da carteira: {pct(k['retorno_medio_carteira'])}")
    linha(f"Ativo destaque: {k['ativo_destaque']} ({pct(k['retorno_ativo_destaque'])})")
    linha(f"Ativo de menor performance: {k['ativo_menor_performance']} ({pct(k['retorno_ativo_menor_performance'])})")
    linha(f"Volatilidade anualizada média: {pct(k['volatilidade_media'])} a.a.")
    linha("\nPor ano:")
    for ano in sorted(base["dt_pregao"].dt.year.unique()):
        ka = kpis_carteira(resumo_por_ativo(base[base["dt_pregao"].dt.year == ano]))
        linha(f"  {ano}: retorno médio {pct(ka['retorno_medio_carteira'])} | vol. média {pct(ka['volatilidade_media'])} | "
              f"melhor {ka['ativo_destaque']} ({pct(ka['retorno_ativo_destaque'])}) | "
              f"pior {ka['ativo_menor_performance']} ({pct(ka['retorno_ativo_menor_performance'])})")

    titulo("P1 · BASE 100 (R$ 100 aplicados no primeiro pregão de 2021)")
    for _, r in resumo.sort_values("vl_retorno_acumulado", ascending=False).iterrows():
        linha(f"{r['cd_ticker']:<7} {r['ds_setor']:<33} R$ 100 -> R$ {num(r['vl_base_100_final'])} | "
              f"acumulado {pct(r['vl_retorno_acumulado'])} | ao ano {pct(r['vl_retorno_anualizado'])}")
    linha(f"Ativos que terminaram acima de 100: {(resumo['vl_base_100_final'] > 100).sum()} de {len(resumo)}")

    titulo("P2 · RISCO x RETORNO (Sharpe empírico = retorno anualizado / volatilidade anualizada)")
    for _, r in resumo.sort_values("vl_indice_sharpe_empirico", ascending=False).iterrows():
        linha(f"{r['cd_ticker']:<7} Sharpe {num(r['vl_indice_sharpe_empirico'])} | volatilidade {pct(r['vl_volatilidade_anualizada'])} a.a. | "
              f"acumulado {pct(r['vl_retorno_acumulado'])} | volume médio R$ {num(r['vl_volume_financeiro_medio'] / 1e6, 1)} mi/dia")

    titulo("P3 · RETORNOS DIÁRIOS (dispersão, assimetria e caudas)")
    linha("Assimetria < 0: quedas extremas mais intensas que as altas. Curtose > 0: mais dias extremos que a curva normal.")
    for _, r in resumo.sort_values("vl_curtose", ascending=False).iterrows():
        linha(f"{r['cd_ticker']:<7} desvio {pct(r['vl_retorno_diario_desvio'], 2)} | pior dia {pct(r['vl_retorno_diario_min'], 2)} | "
              f"melhor dia {pct(r['vl_retorno_diario_max'], 2)} | assimetria {num(r['vl_assimetria'])} | curtose {num(r['vl_curtose'])}")

    titulo("P4 · DRAWDOWN MÁXIMO (do topo ao vale)")
    for _, r in resumo.sort_values("vl_drawdown_maximo", ascending=False).iterrows():
        linha(f"{r['cd_ticker']:<7} {pct(r['vl_drawdown_maximo'])} | topo em {r['dt_topo_antes_drawdown'].date()} | vale em {r['dt_vale_drawdown'].date()}")

    titulo("P5 · PREÇO x MÉDIAS MÓVEIS (SMA 21 e SMA 50)")
    for _, r in resumo.sort_values("pc_pregoes_acima_sma50", ascending=False).iterrows():
        linha(f"{r['cd_ticker']:<7} acima da SMA 50 em {pct(r['pc_pregoes_acima_sma50'])} dos pregões | "
              f"cruzamentos SMA 21 x SMA 50: {r['qt_cruzamentos_sma21_sma50']}")

    titulo("APOIO · SETORES (média simples dos ativos de cada setor)")
    setores = resumo.groupby("ds_setor").agg(
        ativos=("cd_ticker", ", ".join),
        retorno=("vl_retorno_acumulado", "mean"),
        volatilidade=("vl_volatilidade_anualizada", "mean"),
    ).sort_values("retorno", ascending=False)
    for nome, r in setores.iterrows():
        linha(f"{nome:<33} retorno {pct(r['retorno'])} | volatilidade {pct(r['volatilidade'])} | {r['ativos']}")

    titulo("APOIO · CORRELAÇÃO DOS RETORNOS DIÁRIOS (Pearson)")
    corr = matriz_correlacao(base)
    pares = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack().dropna().sort_values(ascending=False)
    linha("Pares mais correlacionados:")
    for (a, b), v in pares.head(5).items():
        linha(f"  {a} x {b}: {num(v)}")
    linha("Pares menos correlacionados:")
    for (a, b), v in pares.tail(5).items():
        linha(f"  {a} x {b}: {num(v)}")
    linha("\nCorrelação não implica causalidade.")
    return "\n".join(L) + "\n"


def main():
    prata = pd.read_csv(config.ARQ_PRATA, parse_dates=["dt_pregao"], encoding="utf-8")
    fato, dim = gerar_camada_ouro(prata)

    config.PASTA_OURO.mkdir(parents=True, exist_ok=True)
    fato.to_csv(config.ARQ_OURO_FATO, index=False, encoding="utf-8", date_format="%Y-%m-%d")
    dim.to_csv(config.ARQ_OURO_DIM, index=False, encoding="utf-8")

    base = juntar_fato_dim(fato, dim)
    resumo = resumo_por_ativo(base)
    resumo.to_csv(config.ARQ_OURO_RESUMO, index=False, encoding="utf-8", date_format="%Y-%m-%d")

    texto = gerar_relatorio(base, resumo)
    config.PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)
    (config.PASTA_RELATORIOS / "relatorio_indicadores.txt").write_text(texto, encoding="utf-8")
    print(texto)
    print(f"Fato: {len(fato)} linhas | Dimensão: {len(dim)} ativos | Resumo: {len(resumo)} ativos")


if __name__ == "__main__":
    main()