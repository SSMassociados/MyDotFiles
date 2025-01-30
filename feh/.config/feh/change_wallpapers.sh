#!/bin/bash

# Caminho da pasta com os wallpapers
WALLPAPER_DIR="/home/sidiclei/wallpaper/"

# Intervalo em segundos para trocar o wallpaper
INTERVAL=300  # 5 minutos

while true; do
    # Escolhe um arquivo aleatório da pasta
    feh --bg-scale "$(find "$WALLPAPER_DIR" -type f | shuf -n 1)"
    sleep "$INTERVAL"
done
