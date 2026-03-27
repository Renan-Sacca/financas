import pandas as pd
from extrator.utils import parse_date, parse_valor, detectar_tipo


def _normalizar_coluna(col) -> str:
    col = str(col).strip().lower()
    for src, dst in [(" ", "_"), ("ã", "a"), ("ç", "c"), ("é", "e"), ("ê", "e"), ("ó", "o"), ("ú", "u"), ("á", "a"), ("í", "i")]:
        col = col.replace(src, dst)
    return col


def _tem_colunas_transacao(header: list[str]) -> bool:
    """Verifica se o cabeçalho contém colunas de data E valor."""
    tem_data = any(any(p in c for p in ("data", "date", "lancamento", "release_date")) for c in header)
    tem_valor = any(any(p in c for p in ("valor", "amount", "value", "montante", "net_amount")) for c in header)
    return tem_data and tem_valor


def parse_xlsx(filepath: str) -> list[dict]:
    """Lê um XLSX e retorna lista de transações normalizadas."""
    xl = pd.ExcelFile(filepath)
    transacoes = []

    for sheet in xl.sheet_names:
        df = xl.parse(sheet, dtype=str, header=None)
        df = df.dropna(how="all")

        # Encontra a linha de cabeçalho real: primeira linha que tenha colunas de data E valor
        header_idx = None
        for i, row in df.iterrows():
            candidate = [_normalizar_coluna(c) for c in row.dropna()]
            if len(candidate) >= 3 and _tem_colunas_transacao(candidate):
                header_idx = i
                break

        if header_idx is None:
            continue

        header = [_normalizar_coluna(c) for c in df.loc[header_idx]]
        data_rows = df.loc[header_idx + 1:]

        for _, row in data_rows.iterrows():
            row = row.where(pd.notna(row), None)
            row_dict = dict(zip(header, row.tolist()))
            t = _mapear_linha(row_dict)
            if t:
                transacoes.append(t)

    return transacoes


def _mapear_linha(row: dict) -> dict | None:
    # Colunas de data
    data_col = next((k for k in row if any(p in k for p in ("data", "date", "release_date", "vencimento"))), None)
    # Colunas de valor (prioriza net_amount sobre saldo)
    valor_col = next((k for k in row if any(p in k for p in ("net_amount", "valor", "amount", "value", "montante"))), None)
    # Colunas de descrição
    desc_col = next((k for k in row if any(p in k for p in ("lancamento", "transaction_type", "descricao", "description", "historico", "memo", "title", "estabelecimento", "beneficiario"))), None)
    # Coluna de tipo entrada/saída (ex: BB)
    tipo_col = next((k for k in row if "tipo" in k and "lancamento" in k), None)

    if not valor_col:
        return None

    raw_valor = row.get(valor_col)
    if raw_valor is None:
        return None

    # Ignora linhas de saldo do dia (data inválida 00/00/0000)
    raw_data = str(row.get(data_col, "") or "") if data_col else ""
    if raw_data.startswith("00/00"):
        return None

    valor = parse_valor(raw_valor)
    if valor == 0.0:
        return None

    raw_desc = str(row.get(desc_col, "") or "")

    # Aplica sinal pela coluna tipo_lancamento se existir (Saída = negativo)
    if tipo_col:
        tipo_lanc = str(row.get(tipo_col, "") or "").lower()
        if "saída" in tipo_lanc or "saida" in tipo_lanc or "debito" in tipo_lanc:
            valor = -abs(valor)
        elif "entrada" in tipo_lanc or "credito" in tipo_lanc:
            valor = abs(valor)

    data = parse_date(raw_data) if data_col else ""

    tipo = detectar_tipo(raw_desc, valor)

    t = {
        "valor": round(abs(valor), 2),
        "data": data,
        "descricao": raw_desc,
        "tipo": tipo,
    }

    # Captura colunas extras relevantes
    for k, v in row.items():
        if k not in (data_col, valor_col, desc_col, tipo_col) and v is not None:
            label = k.strip()
            if label and label not in t:
                t[label] = str(v)

    return t
