#!/usr/bin/python
# Dependências:
#   pip install pdf2docx
#   notify-send  (Linux, via libnotify)
#   paplay       (Linux, via PulseAudio/PipeWire)

import os
import sys
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pdf2docx import Converter

SOUND_PATH = "/usr/share/sounds/freedesktop/stereo/complete.oga"
OUTPUT_FOLDER_NAME = "PDF_to_DOCX"


# ── Conversão de um único arquivo ────────────────────────────────────────────

def convert_one(pdf_file: str, output_folder: str) -> str:
    """Converte um PDF para DOCX. Retorna o caminho do arquivo gerado."""
    if not os.path.isfile(pdf_file):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_file}")
    if not pdf_file.lower().endswith(".pdf"):
        raise ValueError(f"Não é um arquivo PDF: {pdf_file}")

    stem = os.path.splitext(os.path.basename(pdf_file))[0]
    docx_path = os.path.join(output_folder, stem + ".docx")

    cv = Converter(pdf_file)
    try:
        cv.convert(docx_path)   # start=0, end=None são os padrões — omitidos
    finally:
        cv.close()              # garante fechamento mesmo com erro

    return docx_path


# ── Conversão em lote (paralela) ─────────────────────────────────────────────

def pdf_to_docx_batch(pdf_files: list[str]) -> None:
    output_folder = os.path.join(os.getcwd(), OUTPUT_FOLDER_NAME)
    os.makedirs(output_folder, exist_ok=True)   # sem race condition

    total = len(pdf_files)
    succeeded, failed = 0, []

    # Paralelismo: usa N núcleos de CPU (limitado ao nº de arquivos)
    workers = min(os.cpu_count() or 1, total)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(convert_one, f, output_folder): f
            for f in pdf_files
        }

        for i, future in enumerate(as_completed(futures), start=1):
            pdf = futures[future]
            try:
                docx = future.result()
                succeeded += 1
                print(f"[{i}/{total}] ✓  {os.path.basename(pdf)}  →  {docx}")
            except Exception as exc:
                failed += 1
                print(f"[{i}/{total}] ✗  {os.path.basename(pdf)}: {exc}", file=sys.stderr)

    # ── Resumo ────────────────────────────────────────────────────────────────
    print(f"\nConcluído: {succeeded} convertido(s), {len(failed)} falha(s).")

    if succeeded:
        _notify("Conversão Concluída",
                f"{succeeded}/{total} arquivo(s) convertido(s) com sucesso!")
        _play_sound(SOUND_PATH)

    if failed:
        sys.exit(1)   # sinaliza falha parcial para o chamador


# ── Utilitários ───────────────────────────────────────────────────────────────

def _notify(title: str, message: str) -> None:
    """Exibe notificação via notify-send (falha silenciosa se indisponível)."""
    try:
        subprocess.run(
            ["notify-send", title, message],
            check=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        pass   # notify-send ausente ou falhou — não é crítico


def _play_sound(path: str) -> None:
    """Reproduz som via paplay (falha silenciosa se indisponível)."""
    if not os.path.isfile(path):
        return
    try:
        subprocess.run(
            ["paplay", path],
            check=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        pass


# ── Ponto de entrada ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <arquivo1.pdf> [arquivo2.pdf ...]")
        sys.exit(1)

    pdf_to_docx_batch(sys.argv[1:])
