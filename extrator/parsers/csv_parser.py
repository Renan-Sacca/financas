import pandas as pd
from extrator.utils import parse_date, parse_valor, detectar_tipo


def _normalizar_coluna(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("ã", "a").replace("ç", "c").replace("é", "e").replace("ê", "e")


def parse_csv(filepath: str) -> list[dict]:
    """Lê um CSV e retorna lista de transações normalizadas."""
    # Tenta detectar separador automaticamente
    df = pd.read_csv(filepath, sep=None, engine="python", dtype=str, encoding="utf-8-sig")
    df.columns = [_normalizar_coluna(c) for c in df.columns]

    transacoes = []

    for _, row in df.iterrows():
        row = row.where(pd.notna(row), None)
        t = _mapear_linha(row.to_dict(), filepath)
        if t:
            transacoes.append(t)

    return transacoes


def _mapear_linha(row: dict, filepath: str) -> dict | None:
    """Mapeia uma linha do CSV para o formato padrão."""

    # --- Detecta colunas de data ---
    data_col = next((k for k in row if k in ("date", "data", "data_lancamento", "data_transacao")), None)
    # --- Detecta colunas de valor ---
    valor_col = next((k for k in row if k in ("amount", "valor", "value", "montante")), None)
    # --- Detecta colunas de descrição ---
    desc_col = next((k for k in row if k in ("title", "descricao", "description", "historico", "memo", "lancamento")), None)
    # --- Identificador ---
    id_col = next((k for k in row if k in ("identificador", "id", "uuid", "transaction_id")), None)

    if not valor_col:
        return None

    raw_desc = str(row.get(desc_col, "") or "")
    valor = parse_valor(row.get(valor_col))
    data = parse_date(str(row.get(data_col, "") or ""))

    tipo = detectar_tipo(raw_desc, valor)

    t = {
        "valor": round(abs(valor), 2),
        "data": data,
        "descricao": raw_desc,
        "tipo": tipo,
    }
    if id_col and row.get(id_col):
        t["identificador"] = str(row[id_col])

    return t
