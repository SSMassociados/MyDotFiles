#!/bin/bash

# Caminho do script de notificação
SCRIPT_PATH="$HOME/.config/i3/scripts/notificacao_horarios.sh"

# Caminho do arquivo de status
STATUS_FILE="/tmp/notificacao_horarios_status"

# Função para iniciar o script de notificação
start_notificacao() {
    nohup "$SCRIPT_PATH" &> /dev/null &
    echo "ON" > "$STATUS_FILE"
}

# Função para parar o script de notificação
stop_notificacao() {
    pkill -f "$SCRIPT_PATH"
    echo "OFF" > "$STATUS_FILE"
}

# Alterna o estado do script
if pgrep -f "$SCRIPT_PATH" > /dev/null; then
    stop_notificacao
else
    start_notificacao
fi
