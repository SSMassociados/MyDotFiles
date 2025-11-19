#!/usr/bin/env bash

# Pasta de wallpapers
DIR="$HOME/.wallpaper"

# Seleciona um wallpaper aleatório
WALLPAPER=$(find -L "$DIR" -type f \( -iname '*.jpg' -o -iname '*.png' \) | shuf -n 1)

# Verifica se existe
if [[ -z "$WALLPAPER" ]]; then
    notify-send "❌ Nenhum wallpaper encontrado em $DIR"
    exit 1
fi

# Detecta comando do pywal
PYWAL_BIN=$(command -v wal || true)
if [[ -z "$PYWAL_BIN" ]]; then
    notify-send "❌ pywal não encontrado!"
    exit 1
fi

# Detecta comando do feh
FEH_BIN=$(command -v feh || true)
if [[ -z "$FEH_BIN" ]]; then
    notify-send "❌ feh não encontrado!"
    exit 1
fi

# Pywal16?
if "$PYWAL_BIN" --help 2>&1 | grep -q -- '--cols16'; then
    IS_PYWAL16=true
else
    IS_PYWAL16=false
fi

# Evita múltiplos feh abertos
pkill feh 2>/dev/null || true

# Aplica tema com base na versão
if [[ "$IS_PYWAL16" == "true" ]]; then
    # pywal16: usa feh manualmente e modo 16 cores
    "$PYWAL_BIN" -i "$WALLPAPER" --cols16 --backend feh
    feh --bg-fill "$WALLPAPER"
else
    # pywal original: já define o wallpaper e suporta 256+ cores, nesse modo o pywal já chama o feh internamente
    "$PYWAL_BIN" -i "$WALLPAPER" --iterative
fi

# Seta variáveis de cor se existirem. Carrega paleta
[ -f "$HOME/.cache/wal/colors.sh" ] && source "$HOME/.cache/wal/colors.sh"

# Atualiza os serviços que usam cores
"$HOME/.config/dunst/update_dunst_colors.sh"
sleep 0.2
"$HOME/.config/i3/scripts/alttab_pywal.sh"
"$HOME/.config/polybar/launch.sh"
