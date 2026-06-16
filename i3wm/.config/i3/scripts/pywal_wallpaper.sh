#!/usr/bin/env bash
# ==================================================
# PYWAL — Troca wallpaper e propaga cores
# ~/.config/i3/scripts/pywal_wallpaper.sh
#
# Uso:
#   pywal_wallpaper.sh           → wallpaper aleatório
#   pywal_wallpaper.sh /path/img → wallpaper específico
#
# Atalho i3: bindsym $sup+p exec --no-startup-id pywal_wallpaper.sh
# ==================================================

set -uo pipefail

DIR="$HOME/.wallpaper"

# Wallpaper: argumento ou aleatório
if [[ $# -gt 0 && -f "$1" ]]; then
    WALLPAPER="$1"
else
    WALLPAPER=$(find -L "$DIR" -type f \( -iname '*.jpg' -o -iname '*.png' \) | shuf -n 1)
fi

if [[ -z "$WALLPAPER" ]]; then
    notify-send "❌ Pywal" "Nenhum wallpaper encontrado em $DIR"
    exit 1
fi

PYWAL_BIN=$(command -v wal || true)
if [[ -z "$PYWAL_BIN" ]]; then
    notify-send "❌ Pywal" "pywal não encontrado!"
    exit 1
fi

# --- 1. PYWAL: gera cores + aplica wallpaper ---
notify-send -i "$WALLPAPER" "🎨 Pywal" "Aplicando novo tema..."

pkill feh 2>/dev/null || true

if "$PYWAL_BIN" --help 2>&1 | grep -q -- '--cols16'; then
    "$PYWAL_BIN" -i "$WALLPAPER" --cols16 --backend feh
    feh --bg-fill "$WALLPAPER"
else
    "$PYWAL_BIN" -i "$WALLPAPER" --iterative
fi

# --- 2. XRESOURCES: exporta cores para o X11 ---
sleep 0.3
xrdb -merge "$HOME/.cache/wal/colors.Xresources"

# --- 3. Propaga cores para cada serviço individualmente ---
# Cada serviço tem seu próprio script — independente e sem conflito

sleep 0.5
"$HOME/.config/i3/scripts/pywal_dunst.sh" &

sleep 1
"$HOME/.config/i3/scripts/pywal_alttab.sh" &

sleep 1
"$HOME/.config/polybar/pywal_polybar.sh" &

xdo raise -N Polybar
