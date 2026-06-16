#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# =====================================================================
# Script: update_toggle.sh
# Função: Alterna janela scratchpad do Kitty com script específico,
#         recriando-a se outro script for chamado.
# Uso: update_toggle.sh <script_alvo>
# =====================================================================

TERMINAL="${TERMINAL:-kitty}"
CLASS="${CLASS:-update-term}"
SCRIPT="${1:-}"

if [[ -z "$SCRIPT" ]]; then
    echo "Uso: $0 <script_para_executar>"
    exit 2
fi

STATE_FILE="/tmp/${CLASS}_current_script"

# 🧠 Lê o script atualmente em uso (se existir)
CURRENT_SCRIPT="$(cat "$STATE_FILE" 2>/dev/null || echo '')"

# 🧩 Função: cria nova janela
create_window() {
    echo "$SCRIPT" > "$STATE_FILE"
    # Mudado de -lc para -ic para garantir ambiente interativo e leitura de caminhos locais
    $TERMINAL --class="$CLASS" -e bash -ic "$SCRIPT" &

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
        SCRATCH_STATE="hidden"
    else
        SCRATCH_STATE="none"
    fi

    if [[ "$SCRATCH_STATE" == "none" ]]; then
        # Está visível
        if [[ "$SCRIPT" == "$CURRENT_SCRIPT" ]]; then
            # Mesmo script → esconde (toggle normal)
            i3-msg -q "[class=\"$CLASS\"] move scratchpad"
            exit 0
        else
            # Script diferente → fecha e recria
            i3-msg -q "[class=\"$CLASS\"] kill"
            create_window
            exit 0
        fi
    else
        # Está oculta (no scratchpad)
        if [[ "$SCRIPT" == "$CURRENT_SCRIPT" ]]; then
            # Mesmo script → apenas mostra
            i3-msg -q "[class=\"$CLASS\"] scratchpad show, focus"
            exit 0
        else
            # Script diferente → mata janela oculta e recria
            i3-msg -q "[class=\"$CLASS\"] kill"
            create_window
            exit 0
        fi
    fi
else
    # Não existe → cria pela primeira vez
    create_window
fi

exit 0
