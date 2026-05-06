#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# =====================================================================
# Script: dropdown.sh
# Função: Alterna janela scratchpad do Kitty como dropdown terminal
# Uso: dropdown.sh
# =====================================================================

TERMINAL="${TERMINAL:-kitty}"
CLASS="${CLASS:-dropdown-term}"

# 🧩 Função: cria nova janela
create_window() {
    # Apenas terminal, sem comando
    $TERMINAL --class="$CLASS" &

    # Espera janela registrar no i3
    for _ in {1..30}; do
        sleep 0.1
        i3-msg -t get_tree | grep -q "\"class\":\"$CLASS\"" && break
    done

    # Configura posição e tamanho
    i3-msg -q "[class=\"$CLASS\"] floating enable, resize set 100 ppt 25 ppt, move position center, move up 275 px, border none, focus"
}

# 🧩 Se a janela já existe
if i3-msg -t get_tree | grep -q "\"class\":\"$CLASS\""; then
    # Verifica se está dentro do scratchpad
    if i3-msg -t get_tree | jq -e '.. | objects | select(.name=="__i3_scratch") | .. | objects | select(.window_properties? and .window_properties.class=="'"$CLASS"'")' >/dev/null; then
        # Está oculta → mostra
        i3-msg -q "[class=\"$CLASS\"] scratchpad show, focus"
        exit 0
    else
        # Está visível → esconde
        i3-msg -q "[class=\"$CLASS\"] move scratchpad"
        exit 0
    fi
else
    # Não existe → cria pela primeira vez
    create_window
fi

exit 0
