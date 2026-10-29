"""
Data App · Performance de ações da B3 (2021 a 2023).

Uso: streamlit run app.py
"""

import math

import pandas as pd
import plotly.express as px
import streamlit as st

from src import config
from src.indicadores import kpis_carteira, matriz_correlacao, preparar_recorte, resumo_por_ativo

st.set_page_config(
    page_title="Performance de Ações B3 · 2021 a 2023",
    page_icon="📈",
    layout="wide",
)

CORES = config.CORES_ATIVOS
TTL = "1h"
LILAS_ESCURO = "#5E35B1"

ESTILO = """
<style>
h1, h2, h3, h4, [data-testid="stHeading"] * { color: #5E35B1 !important; }
h1 { font-weight: 700; }
[data-testid="stWidgetLabel"] p { color: #5E35B1; font-weight: 600; font-size: 0.95rem; }
[data-testid="stMetric"] { background-color: #FBF9FE; text-align: center; }
[data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
    display: flex; justify-content: center; width: 100%;
}
[data-testid="stMetricValue"] { color: #5E35B1; }
</style>
"""
st.html(ESTILO)

ROTULOS_COLUNAS = {
    "dt_pregao": "Data",
    "cd_ticker": "Ativo",
    "nm_empresa": "Empresa",
    "ds_setor": "Setor",
    "vl_abertura": "Abertura (R$)",
    "vl_maxima": "Máxima (R$)",
    "vl_minima": "Mínima (R$)",
    "vl_fechamento": "Fechamento (R$)",
    "vl_fechamento_ajustado": "Fechamento ajustado (R$)",
    "qt_volume_acoes": "Volume (ações)",
    "vl_volume_financeiro": "Volume financeiro (R$)",
    "vl_retorno_diario": "Retorno diário (%)",
    "vl_sma_21": "SMA 21 (R$)",
    "vl_sma_50": "SMA 50 (R$)",
    "fg_volume_zero": "Sinal: volume zero",
    "fg_variacao_extrema": "Sinal: variação acima de 15%",
}

CONSULTA_SQL = """
SELECT f.*, d.nm_empresa, d.ds_setor
FROM fato_cotacoes AS f
JOIN dim_ativos AS d ON d.cd_ticker = f.cd_ticker
ORDER BY f.cd_ticker, f.dt_pregao
"""


# Dados
@st.cache_resource
def obter_conexao():
    return st.connection("postgresql", type="sql")


@st.cache_data(ttl=TTL, show_spinner="Carregando cotações...")
def carregar_dados():
    try:
        conn = obter_conexao()
        df = conn.query(CONSULTA_SQL, ttl=TTL)
        origem = "banco"
    except Exception:
        fato = pd.read_csv(config.ARQ_OURO_FATO)
        dim = pd.read_csv(config.ARQ_OURO_DIM)
        df = fato.merge(dim[["cd_ticker", "nm_empresa", "ds_setor"]], on="cd_ticker")
        origem = "csv"
    df["dt_pregao"] = pd.to_datetime(df["dt_pregao"])
    return df, origem


@st.cache_data(ttl=TTL, show_spinner="Calculando indicadores...")
def calcular_resumo(df):
    return resumo_por_ativo(df)


@st.cache_data(ttl=TTL, show_spinner=False)
def calcular_recorte(df):
    return preparar_recorte(df)


@st.cache_data(ttl=TTL, show_spinner=False)
def calcular_correlacao(df):
    return matriz_correlacao(df)


@st.cache_data(ttl=TTL, show_spinner=False)
def gerar_csv(df):
    return df.to_csv(index=False, sep=";", decimal=",", date_format="%d/%m/%Y").encode("utf-8-sig")


# Formatação no padrão brasileiro
def sem_zero_negativo(valor, casas):
    return 0.0 if round(valor, casas) == 0 else valor


def pct(valor, casas=1, sinal=False):
    formato = f"{{:{'+' if sinal else ''}.{casas}f}}%"
    return formato.format(sem_zero_negativo(valor * 100, casas)).replace(".", ",")


def num(valor, casas=2):
    valor = sem_zero_negativo(valor, casas)
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pp(diferenca):
    return sem_zero_negativo(round(diferenca * 100, 1), 1)


def texto_pp(valor):
    return f"{valor:+.1f} p.p.".replace(".", ",", 1)


def reais(valor):
    return f"R\\$ {num(valor)}"


def data_br(valor):
    return f"{valor:%d/%m/%Y}"


def padrao_br(fig, datas=True):
    fig.update_layout(separators=",.", title_font_color=LILAS_ESCURO)
    if datas:
        fig.update_xaxes(tickformat="%m/%Y")
    return fig


def qtd(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def storytelling(contexto, insight, acao):
    with st.container(border=True):
        st.markdown(f"**Contexto:** {contexto}\n\n**Insight:** {insight}\n\n**Ação:** {acao}")


def tabela(dados):
    st.dataframe(dados, hide_index=True, width="stretch")


df, origem = carregar_dados()
EMPRESA = df.drop_duplicates("cd_ticker").set_index("cd_ticker")["nm_empresa"].to_dict()


def nome(ticker):
    return f"{ticker} ({EMPRESA[ticker]})"


def ticker_e_empresa(ticker):
    return f"{ticker} · {EMPRESA[ticker]}"


# Filtros
SETORES = sorted(df["ds_setor"].unique())
DATA_MIN = df["dt_pregao"].min().date()
DATA_MAX = df["dt_pregao"].max().date()


def ativos_dos_setores(setores):
    return sorted(df.loc[df["ds_setor"].isin(setores), "cd_ticker"].unique())


def atualizar_ativos():
    st.session_state["filtro_ativos"] = ativos_dos_setores(st.session_state["filtro_setores"])


def limpar_filtros():
    st.session_state["filtro_setores"] = list(SETORES)
    st.session_state["filtro_ativos"] = ativos_dos_setores(SETORES)
    st.session_state["filtro_periodo"] = (DATA_MIN, DATA_MAX)


if "filtro_setores" not in st.session_state:
    limpar_filtros()

with st.sidebar:
    st.header("Filtros")
    st.multiselect(
        "Setores",
        options=SETORES,
        key="filtro_setores",
        on_change=atualizar_ativos,
        placeholder="Selecione os setores",
    )
    st.multiselect(
        "Ativos",
        options=ativos_dos_setores(st.session_state["filtro_setores"]),
        key="filtro_ativos",
        format_func=ticker_e_empresa,
        placeholder="Selecione os ativos",
    )
    st.slider(
        "Período",
        min_value=DATA_MIN,
        max_value=DATA_MAX,
        key="filtro_periodo",
        format="DD/MM/YYYY",
    )
    st.button("Limpar filtros", on_click=limpar_filtros, width="stretch")
    st.divider()
    st.caption("Fonte: Yahoo Finance, via biblioteca yfinance. "
               "Cotações diárias de 04/01/2021 a 28/12/2023.")

setores_sel = st.session_state["filtro_setores"]
ativos_sel = st.session_state["filtro_ativos"]
inicio, fim = st.session_state["filtro_periodo"]

df_periodo = df[df["dt_pregao"].between(pd.Timestamp(inicio), pd.Timestamp(fim))]
df_filtrado = df_periodo[df_periodo["cd_ticker"].isin(ativos_sel)]

# Contexto
st.title("Performance de ações da B3 · 2021 a 2023")
st.markdown("Retorno, risco e tendência de 12 ações de 7 setores da B3, "
            "calculados a partir do preço de fechamento ajustado.")

if origem == "banco":
    st.caption("Dados carregados do PostgreSQL (Supabase).")
else:
    st.warning("Banco de dados indisponível. Dados carregados da cópia local em CSV.")

if df_filtrado.empty:
    st.info("Nenhum dado para os filtros escolhidos. Selecione ao menos um ativo na barra lateral.")
    st.stop()

if (fim - inicio).days < 90:
    st.info("Escolha um período de pelo menos 3 meses para que os indicadores anualizados façam sentido.")
    st.stop()

st.markdown(
    f"**Filtros ativos:** {len(setores_sel)} de {len(SETORES)} setores · "
    f"{qtd(len(ativos_sel), 'ativo', 'ativos')} ({', '.join(ativos_sel)}) · "
    f"{data_br(inicio)} a {data_br(fim)}"
)

resumo = calcular_resumo(df_filtrado)
if resumo.empty:
    st.info("Período muito curto para calcular os indicadores. Amplie o intervalo de datas.")
    st.stop()

recorte = calcular_recorte(df_filtrado)
kpis = kpis_carteira(resumo)
kpis_total = kpis_carteira(calcular_resumo(df_periodo))
dif_retorno = pp(kpis["retorno_medio_carteira"] - kpis_total["retorno_medio_carteira"])
dif_destaque = pp(kpis["retorno_ativo_destaque"] - kpis["retorno_medio_carteira"])
dif_menor = pp(kpis["retorno_ativo_menor_performance"] - kpis["retorno_medio_carteira"])
dif_volatilidade = pp(kpis["volatilidade_media"] - kpis_total["volatilidade_media"])
varios = len(resumo) > 1

por_retorno = resumo.sort_values("vl_retorno_acumulado", ascending=False)
por_sharpe = resumo.sort_values("vl_indice_sharpe_empirico", ascending=False)
por_drawdown = resumo.sort_values("vl_drawdown_maximo", ascending=False)
por_curtose = resumo.sort_values("vl_curtose", ascending=False)
por_sma = resumo.sort_values("pc_pregoes_acima_sma50", ascending=False)
ordem_retorno = list(por_retorno["cd_ticker"])

# KPIs
linha1 = st.columns(2)
linha2 = st.columns(2)

linha1[0].metric(
    "Retorno médio da carteira",
    pct(kpis["retorno_medio_carteira"]),
    delta=f"{texto_pp(dif_retorno)} vs. 12 ativos no mesmo período",
    delta_color="off" if dif_retorno == 0 else "normal",
    help="Média do retorno acumulado dos ativos selecionados, como se o mesmo valor "
         "tivesse sido aplicado em cada um no primeiro pregão do período. "
         "O delta compara com a média dos 12 ativos no mesmo período.",
    border=True,
)
linha1[1].metric(
    f"Ativo destaque · {EMPRESA[kpis['ativo_destaque']]} "
    f"({pct(kpis['retorno_ativo_destaque'], sinal=True)})",
    kpis["ativo_destaque"],
    delta=f"{texto_pp(dif_destaque)} vs. média da carteira",
    delta_color="off" if dif_destaque == 0 else "normal",
    help="Ativo com o maior retorno acumulado no período, pelo fechamento ajustado. "
         "O delta compara o retorno do ativo com o retorno médio da carteira.",
    border=True,
)
linha2[0].metric(
    f"Ativo de menor performance · {EMPRESA[kpis['ativo_menor_performance']]} "
    f"({pct(kpis['retorno_ativo_menor_performance'], sinal=True)})",
    kpis["ativo_menor_performance"],
    delta=f"{texto_pp(dif_menor)} vs. média da carteira",
    delta_color="off" if dif_menor == 0 else "normal",
    help="Ativo com o menor retorno acumulado no período, pelo fechamento ajustado. "
         "O delta compara o retorno do ativo com o retorno médio da carteira.",
    border=True,
)
linha2[1].metric(
    "Volatilidade anualizada média",
    f"{pct(kpis['volatilidade_media'])} a.a.",
    delta=f"{texto_pp(dif_volatilidade)} vs. 12 ativos no mesmo período",
    delta_color="off" if dif_volatilidade == 0 else "inverse",
    help="Média do desvio padrão dos retornos diários, anualizado (x √252). "
         "O delta compara com a média dos 12 ativos no mesmo período: verde indica risco menor.",
    border=True,
)

# Insight e ação
melhor_sharpe = por_sharpe.iloc[0]
mais_resiliente = por_drawdown.iloc[0]
acima_de_100 = int((resumo["vl_base_100_final"] > 100).sum())

with st.container(border=True):
    st.markdown("#### Síntese do período selecionado")
    if varios:
        sintese = (
            f"- **Retorno:** {acima_de_100} de {len(resumo)} ativos terminaram o período valorizados. "
            f"{nome(kpis['ativo_destaque'])} liderou, com {pct(kpis['retorno_ativo_destaque'], sinal=True)}.\n"
            f"- **Retorno ajustado ao risco:** {nome(melhor_sharpe['cd_ticker'])} teve o melhor Sharpe empírico "
            f"({num(melhor_sharpe['vl_indice_sharpe_empirico'])}).\n"
            f"- **Resiliência:** {nome(mais_resiliente['cd_ticker'])} teve a menor queda a partir do topo "
            f"({pct(mais_resiliente['vl_drawdown_maximo'])}).\n"
        )
    else:
        sintese = (
            f"- **Retorno:** {nome(kpis['ativo_destaque'])} variou {pct(kpis['retorno_ativo_destaque'], sinal=True)} no período.\n"
            f"- **Retorno ajustado ao risco:** Sharpe empírico de {num(melhor_sharpe['vl_indice_sharpe_empirico'])}.\n"
            f"- **Resiliência:** queda máxima a partir do topo de {pct(mais_resiliente['vl_drawdown_maximo'])}.\n"
        )
    st.markdown(
        sintese +
        "- **Ação:** ativos que combinam Sharpe alto e drawdown baixo são os candidatos "
        "naturais a um estudo mais aprofundado; ativos com drawdown elevado exigem tolerância a "
        "quedas longas. Os resultados são históricos e não constituem recomendação de investimento."
    )

# Detalhamento por pergunta
aba_base, aba_risco, aba_retornos, aba_drawdown, aba_medias, aba_correlacao, aba_dados = st.tabs(
    ["Base 100", "Risco x retorno", "Retornos diários", "Drawdown", "Médias móveis", "Correlação", "Dados"]
)

with aba_base:
    melhor = por_retorno.iloc[0]
    pior = por_retorno.iloc[-1]
    texto = (f"R\\$ 100 aplicados em {nome(melhor['cd_ticker'])} no início do período "
             f"terminariam em **{reais(melhor['vl_base_100_final'])}**")
    if varios:
        texto += (f"; em {nome(pior['cd_ticker'])}, em **{reais(pior['vl_base_100_final'])}**. "
                  f"{acima_de_100} de {len(resumo)} ativos ficaram acima do nível 100.")
    else:
        texto += "."
    storytelling(
        "se o mesmo valor fosse aplicado em cada ativo no primeiro pregão do período, quanto valeria no fim?",
        texto,
        "retorno isolado não basta para comparar ativos. Confronte estes valores com o risco (aba Risco x "
        "retorno) e com as quedas enfrentadas no caminho (aba Drawdown).",
    )

    fig = px.line(
        recorte, x="dt_pregao", y="vl_base_100", color="cd_ticker", custom_data=["nm_empresa"],
        color_discrete_map=CORES, category_orders={"cd_ticker": ordem_retorno},
        title="Quanto valeriam R$ 100 aplicados em cada ativo no início do período",
        labels={"dt_pregao": "", "vl_base_100": "Valor (R$)", "cd_ticker": "Ativo"},
        height=550,
    )
    fig.add_hline(y=100, line_dash="dash", line_color="#8A94A6",
                  annotation_text="nível 100", annotation_position="bottom right")
    fig.update_traces(line_width=2, hovertemplate="R$ %{y:,.2f} · %{customdata[0]}")
    fig.update_layout(hovermode="x unified", legend_title_text="Ativo (do maior ao menor retorno)")
    st.plotly_chart(padrao_br(fig))
    st.caption("Todos os ativos começam em 100 no primeiro pregão do período. "
               "Acima da linha tracejada, o investimento valorizou; abaixo, perdeu valor. "
               "Clique em um ativo na legenda para ocultá-lo ou dê dois cliques para vê-lo sozinho.")

with aba_risco:
    abertura = "entregou a melhor relação entre retorno e risco:" if varios else "teve"
    texto = (f"{nome(melhor_sharpe['cd_ticker'])} {abertura} "
             f"Sharpe empírico de **{num(melhor_sharpe['vl_indice_sharpe_empirico'])}**, com retorno de "
             f"{pct(melhor_sharpe['vl_retorno_acumulado'])} e volatilidade de "
             f"{pct(melhor_sharpe['vl_volatilidade_anualizada'])} a.a.")
    if varios:
        pior_sharpe = por_sharpe.iloc[-1]
        texto += (f" O menor Sharpe foi de {nome(pior_sharpe['cd_ticker'])}, "
                  f"com {num(pior_sharpe['vl_indice_sharpe_empirico'])}.")
    storytelling(
        "quais ativos entregaram mais retorno por unidade de risco assumido (Sharpe empírico)?",
        texto,
        "ativos com Sharpe baixo ou negativo exigiram mais risco do que remuneraram no período e merecem "
        "revisão em uma carteira que priorize eficiência.",
    )

    dispersao = resumo.assign(
        volatilidade=resumo["vl_volatilidade_anualizada"] * 100,
        retorno=resumo["vl_retorno_acumulado"] * 100,
        volume_mi=resumo["vl_volume_financeiro_medio"] / 1e6,
    )
    fig = px.scatter(
        dispersao, x="volatilidade", y="retorno", size="volume_mi", text="cd_ticker",
        color="cd_ticker", color_discrete_map=CORES, size_max=28,
        title="Retorno acumulado x volatilidade anualizada",
        labels={"volatilidade": "Volatilidade anualizada (% a.a.)", "retorno": "Retorno acumulado (%)",
                "volume_mi": "Volume financeiro médio (R$ mi/dia)",
                "vl_indice_sharpe_empirico": "Sharpe empírico", "nm_empresa": "Empresa"},
        hover_data={"nm_empresa": True, "volatilidade": ":.1f", "retorno": ":.1f", "volume_mi": ":,.1f",
                    "vl_indice_sharpe_empirico": ":.2f", "cd_ticker": False},
        height=550,
    )
    fig.update_traces(textposition="top center", marker_opacity=0.75,
                      marker_line_width=1, marker_line_color="white")
    fig.add_hline(y=0, line_dash="dot", line_color="#8A94A6")
    fig.update_layout(showlegend=False)
    st.plotly_chart(padrao_br(fig, datas=False))
    st.caption("Quanto mais para cima, maior o retorno; quanto mais para a direita, maior o risco. "
               "O tamanho da bolha indica o volume financeiro médio negociado por dia.")

    tabela(pd.DataFrame({
        "Ativo": por_sharpe["cd_ticker"],
        "Empresa": por_sharpe["nm_empresa"],
        "Sharpe empírico": por_sharpe["vl_indice_sharpe_empirico"].map(num),
        "Retorno acumulado": por_sharpe["vl_retorno_acumulado"].map(pct),
        "Retorno anualizado": por_sharpe["vl_retorno_anualizado"].map(pct),
        "Volatilidade anualizada": por_sharpe["vl_volatilidade_anualizada"].map(pct),
    }))
    st.caption("Sharpe empírico = retorno anualizado / volatilidade anualizada, sem desconto da taxa livre de risco.")

with aba_retornos:
    mais_caudas = por_curtose.iloc[0]
    negativos = int((resumo["vl_assimetria"] < 0).sum())
    mais_volatil = resumo.sort_values("vl_retorno_diario_desvio", ascending=False).iloc[0]
    comparacao = "mais" if mais_caudas["vl_curtose"] > 0 else "menos"
    if varios:
        texto = (f"{nome(mais_caudas['cd_ticker'])} tem as caudas mais pesadas (curtose de "
                 f"**{num(mais_caudas['vl_curtose'])}**), ou seja, {comparacao} dias extremos do que uma "
                 f"distribuição normal. {negativos} de {len(resumo)} ativos têm assimetria negativa, com quedas "
                 f"extremas mais intensas que as altas. A maior oscilação diária típica é de "
                 f"{nome(mais_volatil['cd_ticker'])}, com desvio padrão de {pct(mais_volatil['vl_retorno_diario_desvio'], 2)} ao dia.")
    else:
        lado = "quedas extremas mais intensas que as altas" if negativos else "altas extremas mais intensas que as quedas"
        texto = (f"{nome(mais_caudas['cd_ticker'])} tem curtose de **{num(mais_caudas['vl_curtose'])}**, "
                 f"ou seja, {comparacao} dias extremos do que uma distribuição normal, e assimetria de "
                 f"{num(mais_caudas['vl_assimetria'])}, com {lado}. O desvio padrão diário é de "
                 f"{pct(mais_volatil['vl_retorno_diario_desvio'], 2)}.")
    storytelling(
        "como se comportam os retornos diários: dispersão, assimetria e caudas de risco?",
        texto,
        "em ativos com caudas pesadas, a volatilidade média subestima o risco dos dias extremos. "
        "Limites de exposição e diversificação ganham importância.",
    )

    ativo_hist = st.selectbox(
        "Ativo", ordem_retorno,
        index=ordem_retorno.index(kpis["ativo_destaque"]), key="ativo_histograma",
        format_func=ticker_e_empresa,
    )
    dados = recorte[recorte["cd_ticker"] == ativo_hist].dropna(subset=["vl_retorno_periodo"])
    fig = px.histogram(
        dados.assign(retorno=dados["vl_retorno_periodo"] * 100), x="retorno",
        marginal="box", nbins=60, color_discrete_sequence=[CORES[ativo_hist]],
        title=f"{nome(ativo_hist)}: distribuição dos retornos diários",
        labels={"retorno": "Retorno diário (%)"},
        height=480,
    )
    fig.update_layout(yaxis_title="Quantidade de pregões")
    st.plotly_chart(padrao_br(fig, datas=False))
    st.caption("Barras concentradas perto de zero indicam dias de pouca variação. "
               "Os pontos isolados no boxplot são os dias extremos.")

    tabela(pd.DataFrame({
        "Ativo": por_curtose["cd_ticker"],
        "Empresa": por_curtose["nm_empresa"],
        "Desvio padrão diário": por_curtose["vl_retorno_diario_desvio"].map(lambda v: pct(v, 2)),
        "Pior dia": por_curtose["vl_retorno_diario_min"].map(lambda v: pct(v, 2)),
        "Melhor dia": por_curtose["vl_retorno_diario_max"].map(lambda v: pct(v, 2)),
        "Assimetria": por_curtose["vl_assimetria"].map(num),
        "Curtose": por_curtose["vl_curtose"].map(num),
    }))
    st.caption("Assimetria negativa: quedas extremas mais intensas que as altas. "
               "Curtose acima de 0: mais dias extremos do que numa distribuição normal.")

with aba_drawdown:
    abertura = "foi o ativo mais resiliente, com queda máxima de" if varios else "teve queda máxima de"
    texto = (f"{nome(mais_resiliente['cd_ticker'])} {abertura} "
             f"**{pct(mais_resiliente['vl_drawdown_maximo'])}** "
             f"(do topo em {data_br(mais_resiliente['dt_topo_antes_drawdown'])} "
             f"ao vale em {data_br(mais_resiliente['dt_vale_drawdown'])}).")
    if varios:
        menos_resiliente = por_drawdown.iloc[-1]
        texto += (f" A maior queda foi de {nome(menos_resiliente['cd_ticker'])}: "
                  f"{pct(menos_resiliente['vl_drawdown_maximo'])}.")
    storytelling(
        "qual foi a maior queda de cada ativo a partir do topo, e qual se mostrou mais resiliente?",
        texto,
        "o drawdown mostra a perda que o investidor precisaria tolerar. Ativos com quedas maiores exigem "
        "horizonte mais longo e mais tolerância a risco.",
    )

    ordem_drawdown = list(por_drawdown["cd_ticker"])
    colunas = min(3, len(ordem_drawdown))
    linhas = math.ceil(len(ordem_drawdown) / colunas)
    fig = px.area(
        recorte.assign(queda=recorte["vl_drawdown"] * 100),
        x="dt_pregao", y="queda", facet_col="cd_ticker", facet_col_wrap=colunas, custom_data=["nm_empresa"],
        color="cd_ticker", color_discrete_map=CORES,
        category_orders={"cd_ticker": ordem_drawdown},
        title="Queda a partir do topo (do mais ao menos resiliente)",
        labels={"dt_pregao": "", "queda": "Queda (%)"},
        height=160 + 230 * linhas,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_traces(hovertemplate="%{customdata[0]} · %{x|%d/%m/%Y}: %{y:.1f}%<extra></extra>")
    fig.update_layout(showlegend=False)
    st.plotly_chart(padrao_br(fig))
    st.caption("Cada painel mostra quanto o ativo estava abaixo do maior preço já atingido no período. "
               "Zero significa que o ativo estava no topo; o ponto mais baixo é o drawdown máximo.")

    tabela(pd.DataFrame({
        "Ativo": por_drawdown["cd_ticker"],
        "Empresa": por_drawdown["nm_empresa"],
        "Drawdown máximo": por_drawdown["vl_drawdown_maximo"].map(pct),
        "Topo": por_drawdown["dt_topo_antes_drawdown"].map(data_br),
        "Vale": por_drawdown["dt_vale_drawdown"].map(data_br),
    }))

with aba_medias:
    lider_sma = por_sma.iloc[0]
    texto = (f"{nome(lider_sma['cd_ticker'])} fechou acima da SMA 50 em "
             f"**{pct(lider_sma['pc_pregoes_acima_sma50'])}** dos pregões")
    if varios:
        ultimo_sma = por_sma.iloc[-1]
        texto += (f", a tendência de alta mais consistente. No outro extremo, {nome(ultimo_sma['cd_ticker'])} ficou acima da média em "
                  f"{pct(ultimo_sma['pc_pregoes_acima_sma50'])} dos pregões")
    storytelling(
        "como os preços se comportaram frente às médias móveis de 21 e 50 pregões?",
        texto + ".",
        "médias móveis descrevem a tendência passada. Use-as como apoio ao acompanhamento, "
        "não como sinal isolado de compra ou venda.",
    )

    ativo_sma = st.selectbox(
        "Ativo", ordem_retorno,
        index=ordem_retorno.index(kpis["ativo_destaque"]), key="ativo_medias",
        format_func=ticker_e_empresa,
    )
    serie = recorte[recorte["cd_ticker"] == ativo_sma].melt(
        id_vars="dt_pregao", value_vars=["vl_fechamento_ajustado", "vl_sma_21", "vl_sma_50"],
        var_name="serie", value_name="preco",
    )
    serie["serie"] = serie["serie"].map({
        "vl_fechamento_ajustado": "Fechamento ajustado", "vl_sma_21": "SMA 21", "vl_sma_50": "SMA 50",
    })
    fig = px.line(
        serie, x="dt_pregao", y="preco", color="serie",
        color_discrete_map={"Fechamento ajustado": "#7E57C2", "SMA 21": "#FFB74D", "SMA 50": "#81C784"},
        title=f"{nome(ativo_sma)}: fechamento ajustado x SMA 21 x SMA 50",
        labels={"dt_pregao": "", "preco": "Preço (R$)", "serie": ""},
        height=480,
    )
    fig.update_traces(hovertemplate="R$ %{y:,.2f}")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(padrao_br(fig))
    st.caption("Preço acima das médias indica tendência de alta; abaixo, de baixa. "
               "Cada cruzamento da SMA 21 com a SMA 50 marca uma possível mudança de tendência.")

    tabela(pd.DataFrame({
        "Ativo": por_sma["cd_ticker"],
        "Empresa": por_sma["nm_empresa"],
        "Pregões acima da SMA 50": por_sma["pc_pregoes_acima_sma50"].map(pct),
        "Cruzamentos SMA 21 x SMA 50": por_sma["qt_cruzamentos_sma21_sma50"],
    }))

with aba_correlacao:
    if not varios:
        st.info("Selecione ao menos dois ativos para comparar a correlação entre eles.")
    else:
        setor_de = resumo.set_index("cd_ticker")["ds_setor"]
        ordem_setor = sorted(setor_de.index, key=lambda t: (setor_de[t], t))
        corr = calcular_correlacao(df_filtrado).loc[ordem_setor, ordem_setor]

        pares = pd.DataFrame(
            [(a, b, corr.loc[a, b]) for i, a in enumerate(ordem_setor) for b in ordem_setor[i + 1:]],
            columns=["ativo_a", "ativo_b", "correlacao"],
        ).sort_values("correlacao", ascending=False)
        pares["mesmo_setor"] = pares["ativo_a"].map(setor_de) == pares["ativo_b"].map(setor_de)

        mais = pares.iloc[0]
        if len(pares) > 1:
            menos = pares.iloc[-1]
            texto = (f"{nome(mais['ativo_a'])} e {nome(mais['ativo_b'])} foram os ativos que mais se moveram juntos "
                     f"(correlação de **{num(mais['correlacao'])}**); {nome(menos['ativo_a'])} e {nome(menos['ativo_b'])}, "
                     f"os que menos se moveram juntos ({num(menos['correlacao'])}).")
        else:
            texto = (f"{nome(mais['ativo_a'])} e {nome(mais['ativo_b'])} tiveram correlação de "
                     f"**{num(mais['correlacao'])}** entre os retornos diários.")
        if pares["mesmo_setor"].any() and not pares["mesmo_setor"].all():
            media_setor = pares.loc[pares["mesmo_setor"], "correlacao"].mean()
            media_fora = pares.loc[~pares["mesmo_setor"], "correlacao"].mean()
            texto += (f" Ativos do mesmo setor tiveram correlação média de {num(media_setor)}, "
                      f"contra {num(media_fora)} entre setores diferentes.")
        storytelling(
            "quais ativos se movimentaram juntos, e quanto o setor aproxima esses movimentos?",
            texto,
            "para diversificar, combinar ativos de baixa correlação reduz a oscilação conjunta da carteira. "
            "A correlação descreve o movimento conjunto no período, não uma relação de causa.",
        )

        fig = px.imshow(
            corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
            color_continuous_scale=["#F48FB1", "#FFFFFF", "#7E57C2"],
            title="Correlação entre os retornos diários (ativos agrupados por setor)",
            labels={"x": "", "y": "", "color": "Correlação"},
            height=180 + 42 * len(ordem_setor),
        )
        fig.update_traces(hovertemplate="%{y} x %{x}: %{z:.2f}<extra></extra>")
        st.plotly_chart(padrao_br(fig, datas=False))
        st.caption("Correlação de Pearson entre os retornos diários: 1 indica movimentos idênticos, 0 indica "
                   "ausência de relação linear e valores negativos indicam movimentos opostos. "
                   "Correlação mostra que os preços oscilaram juntos, não que um movimento causou o outro.")

        destaque = pares if len(pares) <= 10 else pd.concat([pares.head(5), pares.tail(5)])
        tabela(pd.DataFrame({
            "Par de ativos": destaque["ativo_a"] + " x " + destaque["ativo_b"],
            "Correlação": destaque["correlacao"].map(num),
            "Mesmo setor": destaque["mesmo_setor"].map({True: "Sim", False: "Não"}),
        }))
        if len(pares) > 10:
            st.caption("Os cinco pares mais e os cinco menos correlacionados.")

with aba_dados:
    st.write(f"{num(len(df_filtrado), 0)} registros de {qtd(df_filtrado['cd_ticker'].nunique(), 'ativo', 'ativos')}, "
             "com os filtros aplicados.")
    sinais = ["fg_volume_zero", "fg_variacao_extrema"]
    tela = df_filtrado.assign(vl_retorno_diario=df_filtrado["vl_retorno_diario"] * 100)
    tela[sinais] = tela[sinais].astype(bool)
    colunas_tela = [c for c in ROTULOS_COLUNAS if c in tela.columns]
    numericas = set(tela.select_dtypes("number").columns)
    configuracao = {}
    for coluna in colunas_tela:
        rotulo = ROTULOS_COLUNAS[coluna]
        if coluna == "dt_pregao":
            configuracao[coluna] = st.column_config.DateColumn(rotulo, format="DD/MM/YYYY")
        elif coluna in sinais:
            configuracao[coluna] = st.column_config.CheckboxColumn(rotulo)
        elif coluna in numericas:
            configuracao[coluna] = st.column_config.NumberColumn(rotulo, format="localized")
        else:
            configuracao[coluna] = st.column_config.TextColumn(rotulo)
    st.dataframe(
        tela,
        hide_index=True,
        height=420,
        column_order=colunas_tela,
        column_config=configuracao,
    )
    st.download_button(
        "Baixar dados filtrados (CSV)",
        data=gerar_csv(df_filtrado),
        file_name=f"cotacoes_b3_{inicio:%Y%m%d}_{fim:%Y%m%d}.csv",
        mime="text/csv",
        icon=":material/download:",
    )
    st.caption("Campos vazios nos primeiros pregões de cada ativo são esperados: o retorno depende do pregão "
               "anterior, e as médias móveis, de 21 e 50 pregões de histórico. Pregões atípicos estão "
               "sinalizados nas duas últimas colunas.")
    st.caption("CSV no padrão brasileiro (separador ponto e vírgula e decimal com vírgula), "
               "com os nomes de colunas do dicionário de dados.")

# Metodologia
with st.expander("Sobre os dados e a metodologia"):
    st.markdown(
        """
**Fonte:** cotações diárias do Yahoo Finance, extraídas com a biblioteca yfinance e tratadas
em camadas Bronze (dado bruto), Prata (dado limpo) e Ouro (indicadores), com carga em PostgreSQL.

**Indicadores**
- **Retorno acumulado:** variação do fechamento ajustado entre o primeiro e o último pregão do período.
- **Retorno anualizado:** retorno acumulado convertido para base anual, considerando 252 pregões por ano.
- **Volatilidade anualizada:** desvio padrão dos retornos diários multiplicado por √252.
- **Sharpe empírico:** retorno anualizado dividido pela volatilidade, sem descontar a taxa livre de risco.
- **Drawdown:** queda percentual em relação ao maior preço atingido até aquele dia.
- **SMA 21 e SMA 50:** médias móveis simples de 21 e 50 pregões, calculadas sobre o histórico completo.
- **Correlação:** coeficiente de Pearson entre os retornos diários de cada par de ativos.

**Limitações**
- Desempenho passado não garante resultados futuros, e o painel não é recomendação de investimento.
- A queda de 17,96% da ITUB4 em 04/10/2021 coincide com a cisão da participação do Itaú na XP,
  que o fechamento ajustado do Yahoo Finance não corrige. O registro foi mantido e sinalizado.
- A EMBR3 passou a ser negociada como EMBJ3 em 2025; o histórico foi obtido pelo código atual.
- Correlação entre ativos não implica relação de causa e efeito.

Desenvolvido por Anaysa Pereira Lopes.
        """
    )
