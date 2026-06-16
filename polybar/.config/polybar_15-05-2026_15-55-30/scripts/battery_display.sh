#!/bin/bash

source "$HOME/.cache/wal/colors.sh"

BAT="BAT0"
CAPACITY=$(cat /sys/class/power_supply/$BAT/capacity)
STATUS=$(cat /sys/class/power_supply/$BAT/status)

# Ícones de animação
ICONS=(    )

if [ "$STATUS" = "Charging" ]; then
    # Escolhe a fase conforme o tempo (simulação)
    phase=$(( ($(date +%s) / 1 ) % ${#ICONS[@]} ))
    ICON=${ICONS[$phase]}
    COLOR="$color1"  # ${colors.primary}
    OUTPUT="⚡ $ICON ${CAPACITY}%"
else
    # Sem animação, só ícone por nível
    case $CAPACITY in
        [0-9]|1[0-9]|2[0-4]) ICON=""; COLOR="$color1" ;;
        2[5-9]|3[0-9]) ICON=""; COLOR="$color3" ;;
        4[0-9]|5[0-9]) ICON=""; COLOR="$color2" ;;
        6[0-9]|7[0-9]) ICON=""; COLOR="$color4" ;;
        8[0-9]|9[0-9]|100) ICON=""; COLOR="$color5" ;;
    esac
    OUTPUT="$ICON ${CAPACITY}%"
fi

echo "%{F$COLOR}$OUTPUT%{F-}"
