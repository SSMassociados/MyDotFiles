#!/usr/bin/env bash
# ==================================================
# PYWAL — Atualiza cores do AltTab
# ~/.config/i3/scripts/pywal_alttab.sh
#
# Uso standalone: pywal_alttab.sh
# Chamado por:    pywal_wallpaper.sh
# ==================================================

ALTTAB_SCRIPT="$HOME/.config/i3/scripts/alttab_pywal.sh"

if [[ ! -f "$ALTTAB_SCRIPT" ]]; then
    echo "⚠ Script alttab não encontrado: $ALTTAB_SCRIPT"
    exit 0
fi

"$ALTTAB_SCRIPT"
