#!/usr/bin/env bash

# Seleciona um wallpaper aleatório
WALLPAPER=$(find -L "$HOME/.wallpaper" -type f \( -iname '*.jpg' -o -iname '*.png' \) | shuf -n 1)

# Detecta se é pywal original ou pywal16
PYWAL_BIN=$(command -v wal)
IS_PYWAL16=$("$PYWAL_BIN" --help 2>&1 | grep -q -- '--cols16' && echo "true" || echo "false")

# Aplica tema com base na versão
if [[ "$IS_PYWAL16" == "true" ]]; then
    # pywal16: usa feh manualmente e modo 16 cores
    "$PYWAL_BIN" -i "$WALLPAPER" --cols16 --backend feh
    feh --bg-scale "$WALLPAPER"
else
    # pywal original: já define o wallpaper e suporta 256+ cores
    "$PYWAL_BIN" -i "$WALLPAPER" --iterative
fi

# Seta variáveis de cor se existirem
[ -f "$HOME/.cache/wal/colors.sh" ] && source "$HOME/.cache/wal/colors.sh"

# Atualiza os serviços que usam cores
"$HOME/.config/dunst/update_dunst_colors.sh"
sleep 0.2
"$HOME/.config/i3/scripts/alttab_pywal.sh"
"$HOME/.config/polybar/launch.sh"
