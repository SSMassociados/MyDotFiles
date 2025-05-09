#!/bin/bash

# Nome da janela (padrão Kitty, ajuste se usar outro)
WINDOW_TITLE="BatteryHealth"

# Verifica se já existe uma janela aberta com o nome específico
if pgrep -f "kitty.*--title $WINDOW_TITLE"; then
    # Se já está aberto, mata o processo para fechar
    pkill -f "kitty.*--title $WINDOW_TITLE"
else
    # Se não está aberto, abre uma nova janela com o script
    kitty --title "$WINDOW_TITLE" -e ~/.config/polybar/scripts/battery_health.sh
fi
