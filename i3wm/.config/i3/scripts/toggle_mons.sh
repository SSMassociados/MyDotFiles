#!/bin/bash

# Configurações
STATE_FILE="$HOME/.mons_state"
COMMANDS=("/sbin/mons -o"  "/sbin/mons -s" "/sbin/mons -e top")
DESCRIPTIONS=("Tela Principal" "Tela Secundária" "Tela Estendida ️⬆")
ICONS=("🖥️" "⬆️" "🖥️➡️🖥️")
MONS_PATH="/sbin/mons"
DUNST_TIMEOUT=2000
DUNST_APP_NAME="Monitor Layout"

# Verifica dependências
if ! command -v "$MONS_PATH" &> /dev/null; then
    dunstify -u critical "$DUNST_APP_NAME" "Erro: 'mons' não encontrado em $MONS_PATH"
    exit 1
fi

# Função de notificação melhorada
notify() {
    local icon="$1"
    local message="$2"
    
    if command -v dunstify &> /dev/null; then
        dunstify -u normal -h "string:x-dunst-stack-tag:mons_layout" \
                -i  "$DUNST_APP_NAME" "$icon $message"
    else
        echo -e "$icon $message"
    fi
}

# Verifica estado anterior
if [[ -f "$STATE_FILE" ]]; then
    LAST_INDEX=$(cat "$STATE_FILE")
    [[ "$LAST_INDEX" -ge "${#COMMANDS[@]}" || "$LAST_INDEX" -lt 0 ]] && LAST_INDEX=0
else
    LAST_INDEX=0
fi

# Modo direto via argumento
if [[ "$1" =~ ^[0-9]+$ && "$1" -lt "${#COMMANDS[@]}" ]]; then
    NEXT_INDEX="$1"
elif [[ "$1" == "--status" || "$1" == "-s" ]]; then
    notify "${ICONS[$LAST_INDEX]}" "Status: ${DESCRIPTIONS[$LAST_INDEX]}"
    exit 0
else
    # Ciclo normal
    NEXT_INDEX=$(( (LAST_INDEX + 1) % ${#COMMANDS[@]} ))
fi

# Executa e notifica
if ${COMMANDS[$NEXT_INDEX]}; then
    echo "$NEXT_INDEX" > "$STATE_FILE"
    notify "${ICONS[$NEXT_INDEX]}" "${DESCRIPTIONS[$NEXT_INDEX]}"
else
    notify "⚠️" "Falha ao alterar para ${DESCRIPTIONS[$NEXT_INDEX]}" >&2
    exit 1
fi
