#!/bin/bash

# Mostrar caixa de diálogo para selecionar o nível de compressão
compression=$(zenity --list --radiolist --text="Selecione o nível de compressão:" --column="" --column="Nível" FALSE "/screen" FALSE "/ebook" FALSE "/printer" FALSE "/prepress" --width=400 --height=300)

# Sair se o usuário cancelar a caixa de diálogo
if [ $? != 0 ]; then
    exit
fi

# Iterar sobre cada arquivo selecionado
for file in "$@"; do
    # Verificar se o arquivo é PDF
    if [[ "$(file -b --mime-type "$file")" == application/pdf ]]; then
        # Comprimir o PDF com ghostscript usando a opção de compressão selecionada
        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS="$compression" -dNOPAUSE -dQUIET -dBATCH -sOutputFile="${file%.pdf}_compressed.pdf" "$file"
    else
        zenity --error --text="O arquivo '$file' selecionado não é um PDF."
    fi
done
