#!/usr/bin/env bash

# Obtém todos os PIDs das instâncias da Polybar
PIDS=($(pgrep -u "$UID" -x polybar))

# Verifica se existem ao menos duas instâncias
if [ "${#PIDS[@]}" -lt 2 ]; then
    echo "⚠ Não há uma segunda instância da Polybar em execução!"
    exit 1
fi

# Envia o comando 'toggle' para o PID do monitor secundário
echo ":: Enviando 'toggle' para a Polybar do monitor secundário (PID: ${PIDS[1]})"
polybar-msg -p "${PIDS[1]}" cmd toggle
