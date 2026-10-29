# Dicionário de dados

Prefixos usados nos nomes das colunas:

| Prefixo | Significado |
|---------|-------------|
| `dt_` | data |
| `cd_` | código |
| `nm_` | nome |
| `ds_` | descrição ou categoria |
| `vl_` | valor (preço, índice ou taxa) |
| `qt_` | quantidade |
| `pc_` | proporção |
| `fg_` | sinalizador (1 = sim, 0 = não) |

Tipos primitivos:

| Tipo | Onde | Significado |
|------|------|-------------|
| `str` | pandas | Texto |
| `float64` | pandas | Número decimal de 64 bits |
| `int64` | pandas | Número inteiro de 64 bits |
| `Int64`, `Float64` | pandas | Inteiro e decimal que aceitam valor ausente (tipos anuláveis) |
| `datetime64` | pandas | Data, sem fuso horário |
| `VARCHAR(n)` | PostgreSQL | Texto com até n caracteres |
| `DOUBLE PRECISION` | PostgreSQL | Número decimal de 64 bits |
| `BIGINT` | PostgreSQL | Número inteiro de 64 bits |
| `SMALLINT` | PostgreSQL | Número inteiro pequeno, usado nos sinalizadores |
| `DATE` | PostgreSQL | Data |

Retornos, volatilidade e drawdown ficam gravados em decimal (0,05 = 5%).
A conversão para porcentagem acontece só na exibição.

## Camada Bronze · `data/bronze/cotacoes_brutas_yfinance.csv`

Dado exatamente como veio do yfinance, com três colunas de identificação.

| Campo | Tipo (pandas) | Descrição |
|-------|---------------|-----------|
| `Date` | `str` | Data do pregão com fuso horário (ex.: `2021-01-04 00:00:00-03:00`) |
| `Open` | `float64` | Preço de abertura (R$) |
| `High` | `float64` | Preço máximo do dia (R$) |
| `Low` | `float64` | Preço mínimo do dia (R$) |
| `Close` | `float64` | Preço de fechamento ajustado por desdobramentos e bonificações, sem proventos (R$) |
| `Adj Close` | `float64` | Fechamento ajustado por proventos e desdobramentos (R$) |
| `Volume` | `int64` | Quantidade de ações negociadas |
| `Dividends` | `float64` | Provento pago por ação na data (R$) |
| `Stock Splits` | `float64` | Fator de desdobramento na data (0 = nenhum) |
| `ticker` | `str` | Código do ativo no projeto |
| `simbolo_yahoo` | `str` | Símbolo consultado na API |
| `data_extracao` | `str` | Data e hora do download |

## Camada Prata · `data/prata/cotacoes_tratadas.csv`

Uma linha por ativo por pregão. Mesmas 8.940 linhas da Bronze, sem perda.

| Campo | Tipo (pandas) | Significado | Regra aplicada |
|-------|---------------|-------------|----------------|
| `dt_pregao` | `datetime64` | Dia de negociação | Convertida para datetime, só a data, fuso de Brasília |
| `cd_ticker` | `str` | Código do ativo | Sem espaços, em caixa alta |
| `nm_empresa` | `str` | Nome da companhia | Definido em `src/config.py` |
| `ds_setor` | `str` | Setor econômico | Classificação setorial da B3, em `src/config.py` |
| `vl_abertura` | `float64` | Primeiro preço do dia (R$) | Convertido para número decimal |
| `vl_maxima` | `float64` | Maior preço do dia (R$) | Convertido para número decimal |
| `vl_minima` | `float64` | Menor preço do dia (R$) | Convertido para número decimal |
| `vl_fechamento` | `float64` | Último preço do dia, ajustado por desdobramentos e bonificações, sem proventos (R$) | Convertido para número decimal |
| `vl_fechamento_ajustado` | `float64` | Fechamento corrigido por dividendos, JCP e desdobramentos (R$). Base de todos os indicadores | Convertido para número decimal |
| `qt_volume_acoes` | `Int64` | Ações negociadas no dia | Convertido para número inteiro |
| `vl_volume_financeiro` | `Float64` | Valor negociado no dia, estimado (R$) | `vl_fechamento × qt_volume_acoes` |
| `vl_dividendos` | `float64` | Provento por ação pago na data (R$) | Mantido da fonte |
| `vl_fator_desdobramento` | `float64` | Fator de desdobramento na data | Mantido da fonte |
| `fg_volume_zero` | `int64` | 1 quando o dia veio com volume zero e preços repetidos | Sinalizado, não removido (3 casos) |
| `fg_variacao_extrema` | `int64` | 1 quando a variação diária passou de 15% | Sinalizado, não removido (6 casos) |
| `cd_simbolo_yahoo` | `str` | Símbolo usado na extração | Mantido para auditoria |
| `dt_extracao` | `datetime64` | Data e hora do download | Mantido para auditoria |

## Camada Ouro · modelo estrela

Gravada em CSV (`data/ouro/`) e carregada no PostgreSQL (Supabase) pelo `src/carga_banco.py`,
com a estrutura definida em `src/sql/01_criar_tabelas.sql`.

### `dim_ativos` · uma linha por ativo

| Campo | Tipo (pandas) | Tipo (PostgreSQL) | Significado |
|-------|---------------|-------------------|-------------|
| `cd_ticker` | `str` | `VARCHAR(10)`, chave primária | Código do ativo |
| `nm_empresa` | `str` | `VARCHAR(60)` | Nome da companhia |
| `ds_setor` | `str` | `VARCHAR(60)` | Setor econômico |
| `cd_simbolo_yahoo` | `str` | `VARCHAR(15)` | Símbolo usado na extração |

### `fato_cotacoes` · uma linha por ativo por pregão

Chave primária: `cd_ticker` + `dt_pregao`. Liga-se à `dim_ativos` pelo `cd_ticker` (chave estrangeira).

| Campo | Tipo (pandas) | Tipo (PostgreSQL) | Significado | Regra de cálculo |
|-------|---------------|-------------------|-------------|------------------|
| `dt_pregao` | `datetime64` | `DATE` | Dia de negociação | Da Prata |
| `cd_ticker` | `str` | `VARCHAR(10)` | Código do ativo | Da Prata |
| `vl_abertura` | `float64` | `DOUBLE PRECISION` | Primeiro preço do dia (R$) | Da Prata |
| `vl_maxima` | `float64` | `DOUBLE PRECISION` | Maior preço do dia (R$) | Da Prata |
| `vl_minima` | `float64` | `DOUBLE PRECISION` | Menor preço do dia (R$) | Da Prata |
| `vl_fechamento` | `float64` | `DOUBLE PRECISION` | Último preço do dia, ajustado por desdobramentos e bonificações, sem proventos (R$) | Da Prata |
| `vl_fechamento_ajustado` | `float64` | `DOUBLE PRECISION` | Fechamento ajustado (R$) | Da Prata |
| `qt_volume_acoes` | `int64` | `BIGINT` | Ações negociadas no dia | Da Prata |
| `vl_volume_financeiro` | `float64` | `DOUBLE PRECISION` | Valor negociado no dia, estimado (R$) | Da Prata |
| `vl_retorno_diario` | `float64` | `DOUBLE PRECISION` | Variação em relação ao pregão anterior | `ajustado(t) ÷ ajustado(t−1) − 1`. Vazio no 1º pregão de cada ativo |
| `vl_sma_21` | `float64` | `DOUBLE PRECISION` | Média móvel simples de curto prazo (R$) | Média dos últimos 21 fechamentos ajustados. Vazia nos 20 primeiros pregões |
| `vl_sma_50` | `float64` | `DOUBLE PRECISION` | Média móvel simples de médio prazo (R$) | Média dos últimos 50 fechamentos ajustados. Vazia nos 49 primeiros pregões |
| `fg_volume_zero` | `int64` | `SMALLINT` | Sinalizador de volume zero | Da Prata |
| `fg_variacao_extrema` | `int64` | `SMALLINT` | Sinalizador de variação acima de 15% | Da Prata |

### `resumo_ativos_2021_2023` · uma linha por ativo, período completo

Gravado em `data/ouro/`. No app, este resumo é recalculado a cada filtro.

| Campo | Tipo (pandas) | Significado | Regra de cálculo |
|-------|---------------|-------------|------------------|
| `cd_ticker`, `nm_empresa`, `ds_setor` | `str` | Identificação do ativo | Da dimensão |
| `dt_inicio`, `dt_fim` | `datetime64` | Primeiro e último pregão do período | Mínimo e máximo de `dt_pregao` |
| `qt_pregoes` | `int64` | Quantidade de pregões | Contagem de linhas |
| `vl_preco_inicial`, `vl_preco_final` | `float64` | Fechamento ajustado no 1º e no último pregão (R$) | Da fato |
| `vl_base_100_final` | `float64` | Quanto valeriam R$ 100 aplicados no 1º pregão | `preço final ÷ preço inicial × 100` |
| `vl_retorno_acumulado` | `float64` | Ganho ou perda total no período | `preço final ÷ preço inicial − 1` |
| `vl_retorno_anualizado` | `float64` | Retorno equivalente por ano | `(1 + acumulado) ^ (252 ÷ nº de retornos) − 1` |
| `vl_volatilidade_anualizada` | `float64` | Intensidade das oscilações, em base anual | `desvio padrão dos retornos diários × √252` |
| `vl_indice_sharpe_empirico` | `float64` | Retorno obtido por unidade de risco | `retorno anualizado ÷ volatilidade anualizada` (sem taxa livre de risco) |
| `vl_drawdown_maximo` | `float64` | Maior queda a partir de um topo | `mínimo de (preço ÷ maior preço até a data − 1)` |
| `dt_topo_antes_drawdown`, `dt_vale_drawdown` | `datetime64` | Início e fim da maior queda | Datas do topo e do vale |
| `vl_retorno_diario_medio`, `vl_retorno_diario_desvio` | `float64` | Média e dispersão dos retornos diários | Média e desvio padrão |
| `vl_retorno_diario_min`, `vl_retorno_diario_max` | `float64` | Pior e melhor pregão | Mínimo e máximo |
| `vl_assimetria` | `float64` | Lado das oscilações extremas (negativa = quedas extremas mais intensas que as altas) | `skew()` |
| `vl_curtose` | `float64` | Peso das caudas (acima de 0 = mais dias extremos que a curva normal) | `kurt()`, curtose em excesso |
| `vl_volume_financeiro_medio` | `float64` | Liquidez média diária (R$) | Média do volume financeiro |
| `pc_pregoes_acima_sma50` | `float64` | Fração dos pregões com preço acima da SMA 50 | Só dias em que a SMA 50 existe |
| `qt_cruzamentos_sma21_sma50` | `int64` | Quantas vezes a SMA 21 cruzou a SMA 50 | Troca de sinal de `SMA 21 − SMA 50` |

## Indicadores calculados no Data App

| Indicador | Tipo (pandas) | Regra |
|-----------|---------------|-------|
| Retorno Médio da Carteira | `float64` | Média dos retornos acumulados dos ativos filtrados (mesmo valor em cada um, sem rebalanceamento) |
| Ativo Destaque | `str` | Maior retorno acumulado no filtro |
| Ativo de Menor Performance | `str` | Menor retorno acumulado no filtro |
| Volatilidade Anualizada Média | `float64` | Média das volatilidades anualizadas dos ativos filtrados |
| Correlação entre ativos | `float64` | Coeficiente de Pearson entre os retornos diários de cada par de ativos, de −1 a 1 |