#!/bin/bash
# copy-path.sh — Copia o caminho do arquivo selecionado ou da pasta atual
# Uso pelo Thunar:
#   Com arquivo/pasta selecionado:  copy-path.sh %f
#   Em área vazia:                  copy-path.sh %d

TARGET="${1:-$PWD}"

printf '%s' "$TARGET" | xclip -selection clipboard

command -v notify-send &>/dev/null && \
    notify-send "Caminho copiado" "$TARGET" --icon=edit-copy --expire-time=2000
