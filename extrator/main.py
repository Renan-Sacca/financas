import os
import json
import logging
from pathlib import Path

from extrator.parsers.csv_parser import parse_csv
from extrator.parsers.xlsx_parser import parse_xlsx
from extrator.parsers.pdf_parser import parse_pdf

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

INPUT_DIR = Path("/data/faturas")
OUTPUT_DIR = Path("/data/faturas_json")

PARSERS = {
    ".csv": parse_csv,
    ".xlsx": parse_xlsx,
    ".xls": parse_xlsx,
    ".pdf": parse_pdf,
}


def processar_arquivo(filepath: Path) -> None:
    ext = filepath.suffix.lower()
    parser = PARSERS.get(ext)

    if not parser:
        log.warning(f"Formato não suportado: {filepath.name}")
        return

    log.info(f"Processando: {filepath.name}")
    try:
        transacoes = parser(str(filepath))
        if not transacoes:
            log.warning(f"Nenhuma transação encontrada em: {filepath.name}")
            return

        output_path = OUTPUT_DIR / (filepath.stem + ".json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transacoes, f, ensure_ascii=False, indent=2)

        log.info(f"  -> {len(transacoes)} transações salvas em {output_path.name}")

    except ValueError as e:
        log.warning(f"Ignorado ({filepath.name}): {e}")
    except Exception as e:
        log.error(f"Erro ao processar {filepath.name}: {e}", exc_info=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    arquivos = [
        f for f in INPUT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in PARSERS
    ]

    if not arquivos:
        log.warning(f"Nenhum arquivo encontrado em {INPUT_DIR}")
        return

    log.info(f"Encontrados {len(arquivos)} arquivo(s) para processar.")
    for arquivo in sorted(arquivos):
        processar_arquivo(arquivo)

    log.info("Concluído.")


if __name__ == "__main__":
    main()
