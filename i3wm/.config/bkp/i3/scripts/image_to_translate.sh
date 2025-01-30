#!/bin/bash

# Defina o nome do arquivo de saída
output_file="texto_traduzido.txt"

# Captura uma área específica da tela usando Flameshot GUI
echo "Por favor, selecione a área da tela para capturar..."
flameshot gui -p /tmp/tesseract_screenshot.png

# Verifica se a captura foi realizada com sucesso
if [ $? -ne 0 ]; then
    echo "Erro ao capturar a tela. Saindo..."
    exit 1
fi

# Extrai texto da imagem capturada usando Tesseract OCR
echo "Extraindo texto da imagem..."
text=$(tesseract /tmp/tesseract_screenshot.png stdout)

# Verifica se o texto foi extraído com sucesso
if [ $? -ne 0 ]; then
    echo "Erro ao extrair texto da imagem. Saindo..."
    exit 1
fi

# Quebrar o texto em partes menores (por exemplo, quebra em cada 500 caracteres)
chunk_size=500
text_chunks=$(echo "$text" | fold -w $chunk_size)

# Inicializar o texto traduzido
translated_text=""

# Traduzir cada parte do texto individualmente e concatenar o resultado
for chunk in $text_chunks; do
    echo "Traduzindo parte do texto para Português..."
    translated_chunk=$(wget -qO- "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt-BR&dt=t&q=$chunk" | sed 's/[][]//g' | awk -F'"' '{print $2}')
    translated_text="$translated_text $translated_chunk"
done

# Verifica se o texto traduzido está vazio ou contém apenas caracteres não imprimíveis
if [ -z "$translated_text" ] || [ "$(echo -n "$translated_text" | wc -c)" -le 1 ]; then
    echo "Erro na tradução. O texto traduzido está vazio ou contém apenas caracteres não imprimíveis. Saindo..."
    exit 1
fi

# Salva o texto traduzido em um arquivo
echo "$translated_text" > "$output_file"

# Remove a imagem capturada
rm /tmp/tesseract_screenshot.png

# Exibe a mensagem de conclusão
echo "Texto traduzido salvo em $output_file"
