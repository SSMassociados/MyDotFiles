#!/bin/bash

# Nome da janela (padrão Kitty, ajuste se usar outro)
WINDOW_TITLE="BatteryHealth"
TERMINAL="kitty"  # Altere para seu terminal preferido se necessário

# Verifica se já existe uma janela aberta com o nome específico
if pgrep -f "$TERMINAL.*--title $WINDOW_TITLE"; then
    # Se já está aberto, mata o processo para fechar
    pkill -f "$TERMINAL.*--title $WINDOW_TITLE"
else
    # Se não está aberto, abre uma nova janela com o script detalhado
    $TERMINAL --title "$WINDOW_TITLE" -e ~/.config/polybar/scripts/battery_module.sh
fi
