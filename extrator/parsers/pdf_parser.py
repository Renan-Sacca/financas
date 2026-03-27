import re
import pdfplumber
from extrator.utils import parse_date, parse_valor, detectar_tipo

# Data DD/MM/YYYY ou DD-MM-YYYY no início da linha
RE_DATA_DMY = re.compile(r"^(\d{2}[/\-]\d{2}[/\-]\d{2,4})\s+(.+)$")

# Data "DD MMM YYYY" (ex: "05 FEV 2026") no início da linha
MESES = {"jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
         "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"}
RE_DATA_TEXTO = re.compile(
    r"^(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s+(\d{4})\s*$",
    re.IGNORECASE
)

# Valor monetário "R$ X.XXX,XX"
RE_VALOR = re.compile(r"R\$\s*(-?[\d.,]+)")
RE_VALOR_INLINE = re.compile(r"(-?[\d.,]+)\s*$")

# ID numérico longo
RE_ID = re.compile(r"\b(\d{9,})\b")

# Linha com data curta (DD/MM ou DD/MM no início) + descrição + valor no fim
RE_LINHA_FATURA = re.compile(
    r"^(\d{2}/\d{2})\s+(.+?)\s+(R\$\s*[\d.,]+)\s*$"
)


def parse_pdf(filepath: str) -> list[dict]:
    """Extrai transações de um PDF financeiro."""
    all_lines = []

    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                # Tenta tabelas estruturadas primeiro
                tables = page.extract_tables()
                for table in tables:
                    rows = _processar_tabela(table)
                    if rows:
                        all_lines.extend([("TABLE_ROW", r) for r in rows])
                        continue

                text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                for line in text.split("\n"):
                    all_lines.append(("TEXT", line))
    except Exception as e:
        if "password" in type(e).__name__.lower() or "incorrect" in type(e).__name__.lower():
            raise ValueError(f"PDF protegido por senha: {filepath}") from e
        raise

    # Separa transações já prontas (de tabelas) das linhas de texto
    transacoes = []
    text_lines = []
    for kind, item in all_lines:
        if kind == "TABLE_ROW":
            transacoes.append(item)
        else:
            text_lines.append(item)

    transacoes.extend(_processar_linhas(text_lines))

    # Remove duplicatas
    seen = set()
    unique = []
    for t in transacoes:
        key = (t.get("data"), t.get("valor"), t.get("descricao", "")[:40])
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return unique


def _processar_tabela(table: list) -> list[dict]:
    """Processa tabela extraída pelo pdfplumber."""
    if not table or len(table) < 2:
        return []

    # Encontra a linha de cabeçalho (primeira linha não vazia)
    header_idx = 0
    for i, row in enumerate(table):
        if row and any(c and str(c).strip() for c in row):
            header_idx = i
            break

    header = [str(c or "").strip().lower() for c in table[header_idx]]
    transacoes = []

    for row in table[header_idx + 1:]:
        if not row or all(not c or not str(c).strip() for c in row):
            continue
        cells = [str(c or "").strip() for c in row]
        d = dict(zip(header, cells))
        t = _linha_dict_para_transacao(d)
        if t:
            transacoes.append(t)

    return transacoes


def _linha_dict_para_transacao(row: dict) -> dict | None:
    data_col = next((k for k in row if any(p in k for p in ("data", "date", "dt", "release"))), None)
    valor_col = next((k for k in row if any(p in k for p in ("valor", "amount", "value", "net_amount", "montante"))), None)
    desc_col = next((k for k in row if any(p in k for p in ("descri", "histor", "memo", "movimenta", "transaction_type", "estabele"))), None)

    if not valor_col:
        return None

    raw_valor = row.get(valor_col, "")
    if not raw_valor or raw_valor.strip() in ("", "-"):
        return None

    valor = parse_valor(raw_valor)
    desc = str(row.get(desc_col, "") or "")
    data = parse_date(str(row.get(data_col, "") or "")) if data_col else ""

    return _montar_transacao(valor, desc, data)


def _processar_linhas(lines: list[str]) -> list[dict]:
    """
    Estratégia multi-formato:
    1. Fatura de cartão: DD/MM Descrição R$ valor
    2. Extrato com data DD/MM/YYYY ou DD-MM-YYYY no início
    3. Extrato Nubank PDF: bloco com "DD MMM YYYY" seguido de linhas de transação
    4. Extrato BB: data DD/MM/YYYY com descrição em linhas anteriores
    """
    transacoes = []

    # Tenta formato fatura de cartão (DD/MM + desc + R$ valor)
    fatura = _tentar_fatura_cartao(lines)
    if fatura:
        return fatura

    # Tenta formato Nubank PDF (data por extenso)
    nubank = _tentar_nubank_pdf(lines)
    if nubank:
        return nubank

    # Formato genérico: data no início da linha
    return _tentar_extrato_generico(lines)


def _tentar_fatura_cartao(lines: list[str]) -> list[dict]:
    """Detecta fatura de cartão: linhas com DD/MM + desc + R$ valor."""
    transacoes = []
    for line in lines:
        line = line.strip()
        m = RE_LINHA_FATURA.match(line)
        if m:
            data_str, desc, valor_str = m.group(1), m.group(2).strip(), m.group(3)
            # Data curta DD/MM — assume ano atual
            data = parse_date(data_str + "/2026") if "/" in data_str else parse_date(data_str)
            valor = parse_valor(valor_str)
            t = _montar_transacao(valor, desc, data)
            if t:
                transacoes.append(t)

    return transacoes if len(transacoes) >= 2 else []


def _tentar_nubank_pdf(lines: list[str]) -> list[dict]:
    """
    Formato Nubank PDF:
    'DD MMM YYYY Total de entradas + X.XXX,XX'  <- linha de data com totais
    'Descrição valor'                            <- transação de entrada
    'Total de saídas - X.XXX,XX'
    'Descrição valor'                            <- transação de saída
    'Continuação da descrição'                   <- linha extra sem valor (opcional)
    """
    # Verifica se é formato Nubank PDF (tem linha com "Total de entradas")
    if not any("total de entradas" in l.lower() or "total de saídas" in l.lower() for l in lines):
        return []

    transacoes = []
    data_atual = ""
    modo_saida = False  # True quando estamos após "Total de saídas"
    i = 0

    # Regex para linha de data com totais: "DD MMM YYYY Total de entradas + X"
    RE_DATA_COM_TOTAL = re.compile(
        r"^(\d{1,2})\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\s+(\d{4})\s+total",
        re.IGNORECASE
    )

    while i < len(lines):
        line = lines[i].strip()
        low = line.lower()

        # Linha de data com totais: "05 FEV 2026 Total de entradas + 311,00"
        m = RE_DATA_COM_TOTAL.match(line)
        if m:
            dia, mes_str, ano = m.group(1), m.group(2).lower(), m.group(3)
            mes = MESES.get(mes_str, "01")
            data_atual = f"{dia.zfill(2)}/{mes}/{ano}"
            modo_saida = False
            i += 1
            continue

        # Linha pura de data (sem totais): "DD MMM YYYY"
        m2 = RE_DATA_TEXTO.match(line)
        if m2:
            dia, mes_str, ano = m2.group(1), m2.group(2).lower(), m2.group(3)
            mes = MESES.get(mes_str, "01")
            data_atual = f"{dia.zfill(2)}/{mes}/{ano}"
            modo_saida = False
            i += 1
            continue

        if not data_atual:
            i += 1
            continue

        # Ignora cabeçalho de página repetido (número de conta no formato XXXXXXXX-X)
        if re.match(r"^\d{7,}-\d$", line):
            i += 1
            continue

        # Muda modo para saída
        if "total de saídas" in low or "total de saidas" in low:
            modo_saida = True
            i += 1
            continue

        # Volta para modo entrada
        if "total de entradas" in low:
            modo_saida = False
            i += 1
            continue

        # Ignora linhas de resumo/rodapé e fragmentos de endereço bancário
        if any(k in low for k in ("saldo", "rendimento", "período", "periodo", "extrato gerado",
                                   "tem alguma dúvida", "ouvidoria", "cnpj", "nu financeira",
                                   "nu pagamentos", "asseguramos", "não nos responsabilizamos",
                                   "o saldo líquido", "agência:", "agencia:", "conta:", "cpf",
                                   "movimentações", "movimentacoes", "valores em r$")):
            i += 1
            continue

        # Ignora linhas que são apenas fragmento de conta bancária: "A. (XXXX) Agência: N Conta: N"
        if re.match(r"^[A-Z]\.\s*\(\d+\)", line):
            i += 1
            continue

        # Linha de transação: tem valor no fim
        valor_match = RE_VALOR_INLINE.search(line)
        if valor_match:
            valor_str = valor_match.group(1)
            desc = line[:valor_match.start()].strip()

            if not desc or parse_valor(valor_str) == 0.0:
                i += 1
                continue

            # Próxima linha pode ser continuação da descrição (sem valor)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_low = next_line.lower()
                has_next_valor = bool(RE_VALOR_INLINE.search(next_line))
                is_next_data = bool(RE_DATA_COM_TOTAL.match(next_line) or RE_DATA_TEXTO.match(next_line))
                is_next_total = "total de" in next_low
                if next_line and not has_next_valor and not is_next_data and not is_next_total:
                    desc = desc + " " + next_line
                    i += 1

            valor = parse_valor(valor_str)
            if modo_saida:
                valor = -abs(valor)
            else:
                valor = abs(valor)

            t = _montar_transacao(valor, desc, data_atual)
            if t:
                transacoes.append(t)

        i += 1

    return transacoes if len(transacoes) >= 1 else []


def _tentar_extrato_generico(lines: list[str]) -> list[dict]:
    """
    Extrato com data DD/MM/YYYY ou DD-MM-YYYY no início da linha.
    Suporta formato BB onde a descrição vem na linha ANTERIOR à data.
    Ex:
      'Seguro de Vida'
      '10/03/2026 13013 1780 12,81 (-)'
      'SEGURO DE VIDA'   <- detalhe extra (ignorado ou concatenado)
    """
    transacoes = []
    linha_anterior = ""

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            linha_anterior = ""
            continue

        m = RE_DATA_DMY.match(line)
        if m:
            data_str = m.group(1)
            resto = m.group(2).strip()

            # Monta descrição: linha anterior (se válida) + conteúdo após a data
            if linha_anterior and not _e_linha_ignoravel(linha_anterior):
                desc_full = linha_anterior + " " + resto
            else:
                desc_full = resto

            t = _extrair_transacao_do_bloco(data_str, desc_full)
            if t:
                transacoes.append(t)
            linha_anterior = ""
        else:
            if _e_linha_ignoravel(line):
                linha_anterior = ""
            else:
                linha_anterior = line

    return transacoes


def _extrair_transacao_do_bloco(data_str: str, desc_full: str) -> dict | None:
    # Detecta sinal pelo sufixo (+) ou (-) antes de extrair valor
    sinal = None
    desc_work = desc_full.strip()
    if desc_work.endswith("(-)"):
        sinal = -1
        desc_work = desc_work[:-3].strip()
    elif desc_work.endswith("(+)"):
        sinal = 1
        desc_work = desc_work[:-3].strip()

    valores = RE_VALOR.findall(desc_work)
    if not valores:
        m = RE_VALOR_INLINE.search(desc_work)
        if m:
            valores = [m.group(1)]
        else:
            return None

    valor_str = valores[0]
    valor = parse_valor(valor_str)

    if sinal is not None:
        valor = sinal * abs(valor)

    desc_limpa = RE_VALOR.sub("", desc_work)
    desc_limpa = RE_ID.sub("", desc_limpa)
    desc_limpa = re.sub(r"\s{2,}", " ", desc_limpa).strip().replace("R$", "").strip()
    # Remove valor numérico solto no fim (formato BB sem R$)
    desc_limpa = re.sub(r"\s+\d[\d.,]*\s*$", "", desc_limpa).strip()

    if not desc_limpa or valor == 0.0:
        return None

    data = parse_date(data_str)
    return _montar_transacao(valor, desc_limpa, data)


def _montar_transacao(valor: float, desc: str, data: str) -> dict | None:
    if valor == 0.0 and not desc:
        return None

    tipo = detectar_tipo(desc, valor)

    t = {
        "valor": round(valor, 2),
        "data": data,
        "descricao": desc,
        "tipo": tipo,
    }

    return t


def _e_linha_ignoravel(line: str) -> bool:
    ignorar = [
        "extrato de conta", "periodo:", "entradas:", "saidas:", "saldo",
        "detalhe dos movimentos", "data descrição", "data de geração",
        "você tem alguma dúvida", "mercado pago", "cnpj", "cpf/cnpj",
        "agência", "ligue para", "ouvidoria", "portal de ajuda",
        "www.", "av.", "cep", "1/1", "2/2", "página", "cliente ",
        "lançamentos", "dia lote", "informações adicionais", "limite especial",
        "saldo anterior", "saldo do dia", "emitido em", "vencimento:",
        "detalhes de consumo", "movimentações na fatura", "data movimentações",
        "cartão visa", "total r$", "parcele a fatura", "compras internacionais",
        # BB específico
        "informações complementares", "valor total devido", "valor liberado",
        "despesas-(iof)", "tarifa", "simulação", "sujeitos a confirmação",
        "total aplicações", "saldos por dia", "taxa limite", "tributos",
        "custo efetivo", "data venc", "dias de uso", "juros", "iof *",
        "limite contratado", "limite utilizado", "limite disponivel",
        "credito bb", "data de debito",
    ]
    low = line.lower()
    return any(k in low for k in ignorar)
