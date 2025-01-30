#!/bin/bash

# Verifica se o script já está em execução
if pgrep -x "battery_monitor.sh" > /dev/null
then
    # Se o script já estiver em execução, mata o processo
    pkill -f "battery_monitor.sh"
fi

# Inicia o script de monitoramento de bateria
~/.config/i3/scripts/battery_monitor.sh 
