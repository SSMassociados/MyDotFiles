#!/usr/bin/env bash
# ==================================================
# PYWAL — Atualiza cores da Polybar via IPC
# ~/.config/polybar/pywal_polybar.sh
#
# Recarrega a polybar relendo o colors.ini (via xrdb)
# SEM matar o processo — sem piscar, sem perder a tray
#
# Uso standalone: pywal_polybar.sh
# Chamado por:    pywal_wallpaper.sh
# ==================================================

if ! pgrep -x polybar > /dev/null; then
    echo "⚠ Polybar não está rodando. Iniciando via launch.sh..."
    "$HOME/.config/polybar/launch.sh" &
    exit 0
fi

# Recarrega todas as instâncias via IPC
# O polybar relê o config (incluindo colors.ini via xrdb) sem matar o processo
polybar-msg cmd restart
