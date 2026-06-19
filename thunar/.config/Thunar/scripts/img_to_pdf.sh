#!/bin/bash

# Verifica se o número de argumentos é válido
if [ "$#" -lt 1 ]; then
    echo "Uso: $0 arquivo1.jpg arquivo2.png ..." >&2
    exit 1
fi

# Cria uma pasta de saída se ainda não existir
output_folder="Output_PDF"
mkdir -p "$output_folder"

# Gera um nome único para o arquivo PDF de saída
output_pdf="$output_folder/$(date +%Y-%m-%d_%H-%M-%S).pdf"

# Converte as imagens para PDF usando o convert do ImageMagick
convert "$@" "$output_pdf"

# Verifica se a conversão foi bem-sucedida
if [ $? -eq 0 ]; then
    echo "As imagens foram convertidas para $output_pdf com sucesso!"
else
    echo "Erro ao converter imagens para $output_pdf." >&2
    exit 1
fi
