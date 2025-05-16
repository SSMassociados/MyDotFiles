#!/bin/bash

# Verifica se o gnirehtet está em execução
if pgrep -f "gnirehtet run" > /dev/null; then
    # Desliga o gnirehtet
    pkill -f "gnirehtet run"
    notify-send -i network-wired "Gnirehtet" "Desligado ✅" --urgency=low --hint=string:x-dunst-stack-tag:gnirehtet
    echo "Gnirehtet desligado."
    # Toca um bip curto (2 beeps rápidos)
    beep -f 1000 -l 100 -n -f 800 -l 100
else
    # Liga o gnirehtet
    gnirehtet run > /dev/null 2>&1 &
    notify-send -i network-wired "Gnirehtet" "Ligando... 🌐" --urgency=low --hint=string:x-dunst-stack-tag:gnirehtet
    echo "Gnirehtet ligado. Verifique o dispositivo."
    # Toca um bip de confirmação (som ascendente)
    beep -f 800 -l 100 -n -f 1200 -l 150
fi
