#!/bin/bash

# Configurações
PID_FILE="/tmp/picom.pid"
DUNST_TAG="picom_notification"
CONFIG_FILE="$HOME/.config/picom/picom.conf"

# Função para notificar via Dunst
notify() {
    dunstify -u "$1" -t 2000 -h "string:x-dunst-stack-tag:$DUNST_TAG" "Picom" "$2"
}

# Verifica se o Picom está rodando (via PID file ou pgrep)
if pgrep -x "picom" >/dev/null || [[ -f "$PID_FILE" ]]; then
    # Mata o Picom e processos relacionados
    pkill -9 -x "picom" 2>/dev/null
    pkill -f "start_picom.sh" 2>/dev/null
    rm -f "$PID_FILE" 2>/dev/null
    notify "low" "❌ OFF (Compositor desativado)"
else
    # Inicia o Picom e salva o PID no arquivo
    picom --config "$CONFIG_FILE" --daemon --write-pid-path "$PID_FILE"
    sleep 0.5  # Espera a inicialização
    if pgrep -x "picom" >/dev/null; then
        notify "normal" "✅ ON (PID: $(cat "$PID_FILE"))"
    else
        notify "critical" "⚠️ Falha ao iniciar o Picom!"
    fi
fi
