#!/bin/bash

# Verifica se o autoadb_scrcpy.sh está em execução
if pgrep -f "autoadb_scrcpy.sh" > /dev/null; then
    echo "Encerrando autoadb_scrcpy.sh..."
    pkill -f "autoadb_scrcpy.sh"  # Encerra o script e seus subprocessos
    pkill -f "scrcpy"             # Encerra o scrcpy, se estiver em execução
else
    echo "Iniciando autoadb_scrcpy.sh..."
    ~/.config/i3/scripts/autoadb_scrcpy.sh &  # Inicia o script em segundo plano
fi

