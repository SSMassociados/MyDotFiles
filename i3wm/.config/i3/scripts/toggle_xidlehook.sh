#!/bin/bash

# Configurações
PROCESS_NAME="xidlehook"
START_SCRIPT="$HOME/.config/i3/scripts/start_xidlehook.sh"
PID_FILE="/tmp/xidlehook.pid"
LOCK_FILE="/tmp/xidlehook.lock"
LOG_FILE="/tmp/xidlehook.log"

# Função de notificação melhorada
notify() {
    dunstify -u normal -t 3000 -a "xidlehook" -h string:x-dunst-stack-tag:xidlehook-toggle "Xidlehook" "$1"
}

# Verificação mais robusta do processo
is_running() {
    # Verifica tanto pelo script quanto pelo processo principal
    if pgrep -f "$START_SCRIPT" >/dev/null || pgrep -x "$PROCESS_NAME" >/dev/null; then
        return 0
    else
        # Verifica se o PID no arquivo ainda está ativo
        if [ -f "$PID_FILE" ]; then
            if ps -p $(cat "$PID_FILE") >/dev/null 2>&1; then
                return 0
            else
                # Limpa arquivos de controle se o processo não existir
                rm -f "$PID_FILE" "$LOCK_FILE"
            fi
        fi
        return 1
    fi
}

# Verifica o status atual
if is_running; then
    # Desativa o xidlehook
    pkill -f "$START_SCRIPT" >/dev/null 2>&1
    pkill -x "$PROCESS_NAME" >/dev/null 2>&1
    
    # Remove arquivos de controle
    rm -f "$PID_FILE" "$LOCK_FILE"
    
    # Notificação
    notify "🛑 OFF"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Xidlehook desativado" >> "$LOG_FILE"
else
    # Ativa o xidlehook
    nohup "$START_SCRIPT" >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    touch "$LOCK_FILE"
    
    # Notificação
    notify "✅ ON • PID: $PID"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Xidlehook ativado (PID: $PID)" >> "$LOG_FILE"
    
    # Verificação adicional
    sleep 1
    if ! ps -p $PID >/dev/null 2>&1; then
        notify "⚠️ Erro • Falha ao iniciar"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERRO: Falha ao iniciar xidlehook" >> "$LOG_FILE"
        rm -f "$PID_FILE" "$LOCK_FILE"
    fi
fi

exit 0
