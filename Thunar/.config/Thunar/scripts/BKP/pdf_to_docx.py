#!/usr/bin/env python3

#  Este script requer a instalação das seguintes dependências:
# - O Python geralmente já está instalado na maioria dos sistemas operacionais modernos.
# - pdf2docx: Para a conversão de PDF para DOCX. Pode ser instalado via pip: pip install pdf2docx
# - notify-send: Para exibir notificações visuais no sistema. Normalmente disponível em sistemas Linux com o Dunst ou similar.
# - paplay: Para reproduzir sons no sistema. Normalmente disponível em sistemas Linux com o PulseAudio ou similar.

import os
import sys
import subprocess
from pdf2docx import Converter

def pdf_to_docx_batch(pdf_files):
    # Obtém o diretório atual
    current_directory = os.getcwd()

    # Cria o caminho para a pasta de saída
    output_folder = os.path.join(current_directory, "PDF_to_DOCX")

    # Verifica se a pasta de saída existe e cria se não existir
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Itera sobre os caminhos dos arquivos PDF e converte cada um deles
    for pdf_file in pdf_files:
        # Extrai o nome do arquivo sem a extensão
        pdf_filename, _ = os.path.splitext(os.path.basename(pdf_file))

        # Monta o caminho completo do arquivo DOCX com o mesmo nome do PDF
        docx_path = os.path.join(output_folder, pdf_filename + ".docx")

        # Inicializa o conversor
        cv = Converter(pdf_file)

        # Converte o PDF para DOCX
        cv.convert(docx_path, start=0, end=None)

        # Fecha o conversor
        cv.close()

    # Notifica sobre a conclusão usando Dunst (notify-send) e reproduz um som
    subprocess.run(['notify-send', 'Conversão Concluída', 'Os arquivos foram convertidos com sucesso!'])
    subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'])  # Caminho para o arquivo de som pode variar

if __name__ == "__main__":
    # Verifica se foram fornecidos argumentos suficientes
    if len(sys.argv) < 2:
        print("Uso: {} <arquivo_pdf_1> <arquivo_pdf_2> ...".format(sys.argv[0]))
        sys.exit(1)

    # Lista de caminhos dos arquivos PDF (passados como argumentos)
    pdf_files = sys.argv[1:]

    # Chama a função para converter em lote os arquivos PDF para DOCX
    pdf_to_docx_batch(pdf_files)
