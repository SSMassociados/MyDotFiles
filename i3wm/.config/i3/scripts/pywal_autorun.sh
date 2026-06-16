#!/usr/bin/env bash
# ==================================================
# PYWAL AUTORUN — Login vs Restart do i3
# ~/.config/i3/scripts/pywal_autorun.sh
#
# Login  → polybar não existe → pywal completo
# Restart → polybar existe    → atualiza serviços sem novo wallpaper
# ==================================================

# --- RESTART DO I3: polybar já existe ---
if pgrep -x polybar > /dev/null; then

    # 1. Carrega cores do cache (geradas no último login)
    [ -f "$HOME/.cache/wal/colors.sh" ] && source "$HOME/.cache/wal/colors.sh"
    sleep 0.3

    # 2. Merge no X11 (garante que xrdb está atualizado)
    xrdb -merge "$HOME/.cache/wal/colors.Xresources" 2>/dev/null || true
    sleep 0.5

    # 3. Dunst
    if [ -f "$HOME/.config/i3/scripts/pywal_dunst.sh" ]; then
        "$HOME/.config/i3/scripts/pywal_dunst.sh" &
        sleep 1
    fi

    # 4. Polybar — reload via IPC sem matar o processo
    if [ -f "$HOME/.config/polybar/pywal_polybar.sh" ]; then
        "$HOME/.config/polybar/pywal_polybar.sh" &
    fi
	xdo raise -N Polybar 
    exit 0
fi

# --- LOGIN: pywal completo ---
DIR="$HOME/.wallpaper"
WALLPAPER=$(find -L "$DIR" -type f \( -iname '*.jpg' -o -iname '*.png' \) | shuf -n 1)

if [[ -z "$WALLPAPER" ]]; then
    notify-send "❌ Nenhum wallpaper encontrado em $DIR"
    exit 1
fi

PYWAL_BIN=$(command -v wal || true)
if [[ -z "$PYWAL_BIN" ]]; then
    notify-send "❌ pywal não encontrado!"
    exit 1
fi

FEH_BIN=$(command -v feh || true)
if [[ -z "$FEH_BIN" ]]; then
    notify-send "❌ feh não encontrado!"
    exit 1
fi

pkill feh 2>/dev/null || true

if "$PYWAL_BIN" --help 2>&1 | grep -q -- '--cols16'; then
    "$PYWAL_BIN" -i "$WALLPAPER" --cols16 --backend feh
    feh --bg-fill "$WALLPAPER"
else
    "$PYWAL_BIN" -i "$WALLPAPER" --iterative
fi

[ -f "$HOME/.cache/wal/colors.sh" ] && source "$HOME/.cache/wal/colors.sh"

# Merge no X11
xrdb -merge "$HOME/.cache/wal/colors.Xresources" 2>/dev/null || true
sleep 0.3

# 1. Dunst
if [ -f "$HOME/.config/dunst/update_dunst_colors.sh" ]; then
    "$HOME/.config/dunst/update_dunst_colors.sh" &
    sleep 1
fi

# 2. Polybar — lançamento completo no login
pkill polybar || true
timeout 5 bash -c 'while pgrep -x polybar > /dev/null; do sleep 0.3; done'
if [ -f "$HOME/.config/polybar/launch.sh" ]; then
    "$HOME/.config/polybar/launch.sh" &
fi
