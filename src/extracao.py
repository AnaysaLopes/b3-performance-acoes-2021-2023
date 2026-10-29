"""
Extração das cotações diárias via yfinance (camada Bronze).

Uso: python -m src.extracao
"""

import time
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

from src import config

warnings.filterwarnings("ignore", message=".*inplace keyword.*")

PAUSA_SEGUNDOS = 2
MAX_TENTATIVAS = 3


def baixar_ativo(simbolo):
    """Baixa o histórico diário de um símbolo, com até três tentativas."""
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            df = yf.Ticker(simbolo).history(
                start=config.DATA_INICIO,
                end=config.DATA_FIM_YFINANCE,
                interval="1d",
                auto_adjust=False,
            )
            if not df.empty:
                return df
            raise ValueError("retorno vazio")
        except Exception as erro:
            espera = PAUSA_SEGUNDOS * tentativa * 2
            print(f"   Tentativa {tentativa} falhou ({erro}). Nova tentativa em {espera}s...")
            time.sleep(espera)
    return pd.DataFrame()


def extrair_todos():
    """Extrai todos os ativos configurados em um único DataFrame."""
    data_extracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tabelas = []

    for ticker, info in config.ATIVOS.items():
        simbolo = info["simbolo_yahoo"]
        print(f"Baixando {ticker} ({simbolo})...")

        df = baixar_ativo(simbolo)
        time.sleep(PAUSA_SEGUNDOS)

        if df.empty:
            print(f"   ATENÇÃO: nenhum dado retornado para {ticker}")
            continue

        df = df.reset_index()
        df["ticker"] = ticker
        df["simbolo_yahoo"] = simbolo
        df["data_extracao"] = data_extracao
        tabelas.append(df)
        print(f"   {len(df)} pregões")

    if not tabelas:
        raise RuntimeError("Nenhum ativo foi baixado. Verifique a conexão com a internet.")

    return pd.concat(tabelas, ignore_index=True)


def main():
    config.PASTA_BRONZE.mkdir(parents=True, exist_ok=True)

    df_bruto = extrair_todos()
    df_bruto.to_csv(config.ARQ_BRONZE, index=False, encoding="utf-8")

    print("\n" + "=" * 60)
    print("EXTRAÇÃO CONCLUÍDA · camada Bronze")
    print("=" * 60)
    print(f"Arquivo: {config.ARQ_BRONZE.relative_to(config.RAIZ_PROJETO)}")
    print(f"Linhas: {len(df_bruto)}")
    print(f"Ativos: {df_bruto['ticker'].nunique()} de {len(config.ATIVOS)}")
    print(f"Colunas: {df_bruto.columns.tolist()}")


if __name__ == "__main__":
    main()