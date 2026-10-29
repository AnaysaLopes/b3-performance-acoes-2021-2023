# Perguntas de negócio

**Performance de Ações da B3 · 2021 a 2023**
Autora: Anaysa Pereira Lopes

## Pergunta orientadora

> Entre 2021 e 2023, quais das 12 ações analisadas entregaram o melhor retorno
> para o risco que cobraram do investidor, e quais mostraram mais resiliência
> nas quedas?

## Recorte

| Item | Definição |
|------|-----------|
| Período | 01/01/2021 a 31/12/2023 (série diária) |
| Ativos | WEGE3, EMBR3, VALE3, GGBR4, KLBN11, PETR4, PRIO3, EGIE3, ITUB4, BBDC4, ABEV3, RENT3 |
| Fonte | Histórico diário de cotações do Yahoo Finance, via biblioteca yfinance (sufixo .SA) |
| Variáveis | Data, abertura, máxima, mínima, fechamento ajustado e volume financeiro |

## As cinco perguntas de negócio

| # | Pergunta | História de usuário | Visual |
|---|----------|---------------------|--------|
| P1 | Se um investidor aplicasse capital em cada ativo no início de 2021, qual seria a rentabilidade comparativa normalizada (Base 100) acumulada até o final de 2023? | Como investidora, quero ver todos os ativos partindo do mesmo ponto (100), para comparar o desempenho sem a distorção do preço de cada ação. | Linha Base 100 com referência no nível 100 |
| P2 | Quais ativos entregaram a melhor relação de Sharpe empírica (maior retorno acumulado com menor volatilidade histórica anualizada)? | Como investidora, quero comparar retorno e volatilidade no mesmo gráfico, para saber quais ativos pagaram melhor pelo risco. | Dispersão risco x retorno, com tamanho pelo volume |
| P3 | Como se comportam estatisticamente os retornos diários dos ativos (dispersão, assimetria e caudas de risco de mercado)? | Como analista de risco, quero ver a distribuição dos retornos diários, para identificar quais ativos têm oscilações extremas com mais frequência. | Histograma com boxplot marginal |
| P4 | Qual foi o drawdown máximo percentual enfrentado por cada papel a partir de seu pico histórico e qual ativo se mostrou mais resiliente? | Como investidora, quero saber a maior queda que cada ação sofreu a partir do topo, para entender a perda que eu teria que suportar. | Área de drawdown |
| P5 | Como os preços de fechamento se comportaram frente às médias móveis simples (SMA 21 e SMA 50)? | Como investidora, quero ver o preço junto das médias móveis de um ativo, para inspecionar a tendência de curto e médio prazo. | Multilinha preço, SMA 21 e SMA 50 |

Como apoio às perguntas, o Data App também mostra a correlação entre os
retornos diários dos ativos e compara a correlação dentro de um mesmo setor com
a correlação entre setores diferentes.

## KPIs estratégicos

Retorno médio da carteira (%), ativo destaque (melhor performance), ativo de
menor performance e volatilidade anualizada média (% a.a.).

## Cuidados na interpretação

As respostas descrevem o que aconteceu entre 2021 e 2023. Não são previsão de
desempenho futuro, e nenhuma relação entre variáveis é tratada como causa e
efeito sem comprovação estatística.
