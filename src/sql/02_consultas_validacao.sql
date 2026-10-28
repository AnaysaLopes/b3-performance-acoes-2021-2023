-- Validação da carga e consultas analíticas da camada Ouro

-- 1. Pregões e período por ativo
SELECT
    f.cd_ticker,
    d.ds_setor,
    COUNT(*)         AS qt_pregoes,
    MIN(f.dt_pregao) AS dt_inicio,
    MAX(f.dt_pregao) AS dt_fim
FROM fato_cotacoes f
JOIN dim_ativos d ON d.cd_ticker = f.cd_ticker
GROUP BY f.cd_ticker, d.ds_setor
ORDER BY f.cd_ticker;

-- 2. Integridade: cotações sem ativo na dimensão (esperado: nenhuma linha)
SELECT f.cd_ticker, COUNT(*) AS qt_linhas
FROM fato_cotacoes f
LEFT JOIN dim_ativos d ON d.cd_ticker = f.cd_ticker
WHERE d.cd_ticker IS NULL
GROUP BY f.cd_ticker;

-- 3. Retorno acumulado por ativo no período
SELECT DISTINCT
    cd_ticker,
    ROUND((
        LAST_VALUE(vl_fechamento_ajustado) OVER w
        / FIRST_VALUE(vl_fechamento_ajustado) OVER w - 1
    )::numeric * 100, 2) AS pc_retorno_acumulado
FROM fato_cotacoes
WINDOW w AS (PARTITION BY cd_ticker ORDER BY dt_pregao
             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
ORDER BY pc_retorno_acumulado DESC;

-- 4. Volatilidade anualizada por ativo (% a.a.)
SELECT
    cd_ticker,
    ROUND((STDDEV_SAMP(vl_retorno_diario) * SQRT(252) * 100)::numeric, 2) AS pc_volatilidade_anualizada
FROM fato_cotacoes
GROUP BY cd_ticker
ORDER BY pc_volatilidade_anualizada;

-- 5. Volume financeiro médio diário por setor (R$ milhões)
SELECT
    d.ds_setor,
    ROUND((AVG(f.vl_volume_financeiro) / 1e6)::numeric, 1) AS vl_volume_medio_mi
FROM fato_cotacoes f
JOIN dim_ativos d ON d.cd_ticker = f.cd_ticker
GROUP BY d.ds_setor
ORDER BY vl_volume_medio_mi DESC;