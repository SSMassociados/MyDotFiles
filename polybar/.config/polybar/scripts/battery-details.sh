#!/bin/bash

# Configurações
TOGGLE_FILE="/tmp/battery_health_visible"
#ROFI_THEME="-theme ~/.config/polybar/scripts/rofi-battery.rasi"

# Função para obter informações da bateria
get_battery_info() {
    BATTERY=$(upower -e | grep -i battery | head -1)
    INFO=$(upower -i "$BATTERY")
    
    STATE=$(echo "$INFO" | grep -E "state:" | awk '{print $2}')
    PERCENTAGE_NUM=$(echo "$INFO" | grep -E "percentage:" | awk '{print $2}' | tr -d '%')
    ENERGY_FULL=$(echo "$INFO" | grep -E "energy-full:" | awk '{print $2}')
    ENERGY_FULL_DESIGN=$(echo "$INFO" | grep -E "energy-full-design:" | awk '{print $2}')
    
    # Cálculo da saúde
    if [ -n "$ENERGY_FULL" ] && [ -n "$ENERGY_FULL_DESIGN" ]; then
        HEALTH=$(awk -v ef="$ENERGY_FULL" -v efd="$ENERGY_FULL_DESIGN" 'BEGIN {printf "🔋 Saúde da Bateria\n\n📊 Capacidade Atual: %.1f%%\n💡 Design Original: %.1f Wh\n⚡ Estado: %s", (ef/efd)*100, efd, "'"$STATE"'"}')
    else
        HEALTH="🔋 Informações não disponíveis"
    fi
    
    echo "$STATE $PERCENTAGE_NUM $HEALTH"
}

# Processa o clique do mouse
handle_click() {
    case "$1" in
        right)
            if [ -f "$TOGGLE_FILE" ]; then
                rm "$TOGGLE_FILE"
                # Mostra informações no Rofi
                echo "$HEALTH" | rofi -dmenu -p "Battery Health" $ROFI_THEME -display-columns 0
            else
                touch "$TOGGLE_FILE"
            fi
            ;;
    esac
}

# Main
read STATE PERCENTAGE_NUM HEALTH <<< $(get_battery_info)

# Se receber argumento (clique do mouse)
if [ -n "$1" ]; then
    handle_click "$1"
    exit 0
fi

# Define cores e ícones
if [ "$STATE" = "charging" ]; then
    ICON="⚡"
    COLOR="#FFFF00"
else
    ICON="🔋"
    if [ "$PERCENTAGE_NUM" -ge 70 ]; then
        COLOR="#00FF00"
    elif [ "$PERCENTAGE_NUM" -ge 30 ]; then
        COLOR="#FFFFFF"
    else
        COLOR="#FF0000"
    fi
fi

# Saída normal (sem saúde)
echo "%{A1:}%{A3:$0 right:}%{F$COLOR}$ICON $PERCENTAGE_NUM%%{F-}%{A}%{A}"
