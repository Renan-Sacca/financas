import re
from datetime import datetime


DATE_FORMATS = [
    "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
    "%d/%m/%y", "%d.%m.%Y", "%Y%m%d",
]


def parse_date(value: str) -> str:
    """Tenta converter uma string de data para DD/MM/AAAA."""
    if not value:
        return ""
    value = str(value).strip()
    # Remove hora se vier junto
    value = re.split(r"[\sT]", value)[0]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return value


def parse_valor(value) -> float:
    """Converte string de valor para float."""
    if value is None:
        return 0.0
    s = str(value).strip()
    # Remove símbolo de moeda e espaços
    s = re.sub(r"[R$\s]", "", s)
    # Trata formato brasileiro: 1.234,56
    if re.match(r"^-?\d{1,3}(\.\d{3})*(,\d+)?$", s):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def detectar_tipo(descricao: str, valor: float = 0.0) -> str:
    """Infere o tipo da transação pela descrição."""
    desc = descricao.lower() if descricao else ""

    if any(k in desc for k in ["pix", "transferência", "transferencia"]):
        return "pix"
    if any(k in desc for k in ["ted", "doc"]):
        return "ted"
    if any(k in desc for k in ["cartão", "cartao", "parcela", "compra"]):
        return "cartao_credito"
    if any(k in desc for k in ["boleto", "pagamento de boleto"]):
        return "boleto"
    if any(k in desc for k in ["aplicação", "aplicacao", "rdb", "cdb", "investimento", "rendimento"]):
        return "investimento"
    if any(k in desc for k in ["saque", "atm"]):
        return "saque"
    if any(k in desc for k in ["débito", "debito"]):
        return "debito"
    if any(k in desc for k in ["fatura", "pagamento de fatura"]):
        return "pagamento_fatura"
    if any(k in desc for k in ["depósito", "deposito"]):
        return "deposito"
    if any(k in desc for k in ["iof"]):
        return "iof"
    return "outros"


def extrair_banco(texto: str) -> str:
    """Tenta extrair nome do banco de uma descrição."""
    if not texto:
        return ""
    # Padrão: "BCO NOME (XXXX)" ou "Banco Nome"
    match = re.search(r"BCO\s+([\w\s\.]+?)\s*\((\d+)\)", texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"banco\s+([\w\s]+)", texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Bancos conhecidos por nome
    bancos = {
        "nubank": "Nubank", "itaú": "Itaú", "itau": "Itaú",
        "bradesco": "Bradesco", "santander": "Santander",
        "caixa": "Caixa Econômica Federal", "bb": "Banco do Brasil",
        "inter": "Banco Inter", "c6": "C6 Bank", "mercado pago": "Mercado Pago",
        "picpay": "PicPay", "sicoob": "Sicoob", "sicredi": "Sicredi",
        "btg": "BTG Pactual", "xp": "XP Investimentos",
    }
    lower = texto.lower()
    for key, nome in bancos.items():
        if key in lower:
            return nome
    return ""
