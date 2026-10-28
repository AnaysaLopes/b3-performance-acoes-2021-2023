"""
Carga da camada Ouro no PostgreSQL (Supabase).
Credenciais lidas de .streamlit/secrets.toml.

Uso: python -m src.carga_banco
"""

import tomllib

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from src import config

ARQ_SECRETS = config.RAIZ_PROJETO / ".streamlit" / "secrets.toml"
ARQ_DDL = config.RAIZ_PROJETO / "src" / "sql" / "01_criar_tabelas.sql"


def criar_engine():
    with open(ARQ_SECRETS, "rb") as f:
        c = tomllib.load(f)["connections"]["postgresql"]
    url = URL.create(
        "postgresql+psycopg2",
        username=c["username"],
        password=c["password"],
        host=c["host"],
        port=int(c["port"]),
        database=c["database"],
    )
    return create_engine(url)


def executar_ddl(conn):
    sql = "\n".join(l for l in ARQ_DDL.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--"))
    for comando in (c.strip() for c in sql.split(";")):
        if comando:
            conn.execute(text(comando))


def main():
    fato = pd.read_csv(config.ARQ_OURO_FATO, parse_dates=["dt_pregao"])
    dim = pd.read_csv(config.ARQ_OURO_DIM)
    fato["dt_pregao"] = fato["dt_pregao"].dt.date

    with criar_engine().begin() as conn:
        executar_ddl(conn)
        dim.to_sql("dim_ativos", conn, if_exists="append", index=False)
        fato.to_sql("fato_cotacoes", conn, if_exists="append", index=False, method="multi", chunksize=1000)
        linhas_banco = conn.execute(text("SELECT COUNT(*) FROM fato_cotacoes")).scalar()
        ativos_banco = conn.execute(text("SELECT COUNT(*) FROM dim_ativos")).scalar()

    print(f"dim_ativos:    {ativos_banco} linhas no banco | {len(dim)} no CSV")
    print(f"fato_cotacoes: {linhas_banco} linhas no banco | {len(fato)} no CSV")
    print("Carga conferida." if linhas_banco == len(fato) and ativos_banco == len(dim) else "Divergência na carga.")


if __name__ == "__main__":
    main()