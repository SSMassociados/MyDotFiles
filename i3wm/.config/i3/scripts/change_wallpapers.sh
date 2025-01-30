#!/bin/bash

# Lê as configurações do Matugen
CONFIG_FILE="$HOME/.config/matugen/config.toml"
COMMAND=$(grep -A 1 "\[config.wallpaper\]" "$CONFIG_FILE" | grep "command" | cut -d'"' -f2)
ARGUMENTS=$(grep -A 1 "\[config.wallpaper\]" "$CONFIG_FILE" | grep "arguments" | cut -d'"' -f2)
INTERVAL=$(grep -A 1 "\[config.wallpaper\]" "$CONFIG_FILE" | grep "interval" | grep -oE '[0-9]+')
DIRECTORY=$(grep -A 1 "\[config.wallpaper\]" "$CONFIG_FILE" | grep "directory" | cut -d'"' -f2)

# Define valores padrão caso as opções não sejam configuradas
COMMAND=${COMMAND:-feh}
ARGUMENTS=${ARGUMENTS:-"--bg-scale"}
INTERVAL=${INTERVAL:-300}
DIRECTORY=${DIRECTORY:-"$HOME/wallpapers"}

# Loop para trocar os wallpapers
while true; do
    # Seleciona um wallpaper aleatório do diretório
    WALLPAPER=$(find "$DIRECTORY" -type f | shuf -n 1)

    # Aplica o wallpaper
    $COMMAND $ARGUMENTS "$WALLPAPER"

    # Aguarda até a próxima troca
    sleep "$INTERVAL"
done
