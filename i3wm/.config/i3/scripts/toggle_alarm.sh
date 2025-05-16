#!/bin/bash

# Verifica se o alarm-clock-applet está em execução (usando -f para checar a linha de comando completa)
if pgrep -f "alarm-clock-applet" > /dev/null; then
    pkill -f "alarm-clock-applet"
else
    alarm-clock-applet &
fi
