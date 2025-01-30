#!/bin/bash

# Verifica se o diretório PDF_to_DOC existe, caso contrário, cria-o
mkdir -p PDF_to_DOC

# Verifica se foram passados os arquivos PDF de entrada como argumentos
if [ "$#" -eq 0 ]; then
    echo "Uso: $0 arquivo_pdf_entrada1 [arquivo_pdf_entrada2 ...]"
    exit 1
fi

# Loop sobre todos os arquivos PDF de entrada
for arquivo_pdf_entrada in "$@"; do
    # Verifica se o arquivo PDF de entrada existe
    if [ ! -f "$arquivo_pdf_entrada" ]; then
        echo "Aviso: O arquivo de entrada $arquivo_pdf_entrada não foi encontrado, pulando para o próximo."
        continue
    fi
    
    # Extrai o nome do arquivo (sem extensão)
    nome_arquivo=$(basename "$arquivo_pdf_entrada" .pdf)

    # Nome do arquivo de saída DOC
    arquivo_doc_saida="PDF_to_DOC/${nome_arquivo}.doc"

    # Realiza a conversão de PDF para DOC usando o LibreOffice headless
    libreoffice --headless --convert-to doc "$arquivo_pdf_entrada" --outdir PDF_to_DOC

    # Verifica se a conversão foi bem-sucedida
    if [ $? -eq 0 ]; then
        echo "Conversão concluída com sucesso: $arquivo_doc_saida"
        # Notificação visual
        dunstify "Conversão concluída" "PDF para DOC: $arquivo_doc_saida" -u normal
        # Notificação sonora
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga
    else
        echo "Erro ao converter o arquivo PDF para DOC: $arquivo_pdf_entrada."
    fi
done

exit 0
