#!/bin/bash

# Diretório contendo as imagens de papel de parede
wallpaper_dir="$HOME/.wallpaper/"

# Verifica se o diretório de papéis de parede existe
if [ ! -d "$wallpaper_dir" ]; then
    echo "O diretório $wallpaper_dir não existe."
    exit 1
fi

# Seleciona aleatoriamente uma imagem do diretório
random_wallpaper=$(find "$wallpaper_dir" -type f \( -name "*.jpg" -o -name "*.png" \) -print0 | shuf -n 1 -z)

# Verifica se uma imagem foi encontrada
if [ -z "$random_wallpaper" ]; then
    echo "Nenhuma imagem de papel de parede encontrada no diretório $wallpaper_dir."
    exit 1
fi

# Executa o betterlockscreen com a imagem selecionada aleatoriamente
betterlockscreen -u "$random_wallpaper" -l dim
