-- Camada Ouro no PostgreSQL (Supabase): modelo estrela

DROP TABLE IF EXISTS fato_cotacoes;
DROP TABLE IF EXISTS dim_ativos;

CREATE TABLE dim_ativos (
    cd_ticker         VARCHAR(10) PRIMARY KEY,
    nm_empresa        VARCHAR(60) NOT NULL,
    ds_setor          VARCHAR(60) NOT NULL,
    cd_simbolo_yahoo  VARCHAR(15) NOT NULL
);

CREATE TABLE fato_cotacoes (
    dt_pregao               DATE             NOT NULL,
    cd_ticker               VARCHAR(10)      NOT NULL REFERENCES dim_ativos (cd_ticker),
    vl_abertura             DOUBLE PRECISION NOT NULL,
    vl_maxima               DOUBLE PRECISION NOT NULL,
    vl_minima               DOUBLE PRECISION NOT NULL,
    vl_fechamento           DOUBLE PRECISION NOT NULL,
    vl_fechamento_ajustado  DOUBLE PRECISION NOT NULL,
    qt_volume_acoes         BIGINT           NOT NULL,
    vl_volume_financeiro    DOUBLE PRECISION NOT NULL,
    vl_retorno_diario       DOUBLE PRECISION,
    vl_sma_21               DOUBLE PRECISION,
    vl_sma_50               DOUBLE PRECISION,
    fg_volume_zero          SMALLINT         NOT NULL,
    fg_variacao_extrema     SMALLINT         NOT NULL,
    PRIMARY KEY (cd_ticker, dt_pregao)
);

CREATE INDEX idx_fato_cotacoes_data ON fato_cotacoes (dt_pregao);