#!/bin/bash
# toggle_rmpc.sh - Versão simplificada com notificações

PID_FILE="/tmp/rmpc.pid"
CMD="kitty --class=RMPC -e rmpc"  # Comando completo com terminal

# Função de notificação melhorada
notify() {
    dunstify -u "$1" -t 3000 --icon="audio-headphones" -a "RMPC" -h string:x-dunst-stack-tag:rmpc-toggle "$2" 
}

# Verifica se já está rodando
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" && rm "$PID_FILE"
        notify "low" "🎵 RMPC 🎶 ⏹️"
        exit 0
    else
        rm "$PID_FILE"
    fi
fi

# Inicia novo processo
$CMD &
echo $! > "$PID_FILE"
notify "low" "🎵 RMPC 🎶 ▶️"

# Configurações de janela devem estar no i3config
