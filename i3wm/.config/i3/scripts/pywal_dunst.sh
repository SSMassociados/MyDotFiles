#!/usr/bin/env bash
# ==================================================
# PYWAL — Atualiza cores do Dunst
# ~/.config/i3/scripts/pywal_dunst.sh
#
# Uso standalone: pywal_dunst.sh
# Chamado por:    pywal_wallpaper.sh
# ==================================================

DUNST_SCRIPT="$HOME/.config/dunst/update_dunst_colors.sh"

if [[ ! -f "$DUNST_SCRIPT" ]]; then
    echo "⚠ Script dunst não encontrado: $DUNST_SCRIPT"
    exit 0
fi

"$DUNST_SCRIPT"
