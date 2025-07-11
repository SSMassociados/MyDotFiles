#!/bin/bash

source "$HOME/.cache/wal/colors.sh"

BAT="BAT0"

CAPACITY=$(cat /sys/class/power_supply/$BAT/capacity)
STATUS=$(cat /sys/class/power_supply/$BAT/status)

HEALTH="N/A"
if [ -f /sys/class/power_supply/$BAT/charge_full_design ]; then
    FULL=$(cat /sys/class/power_supply/$BAT/charge_full)
    DESIGN=$(cat /sys/class/power_supply/$BAT/charge_full_design)
    if [ "$DESIGN" -gt 0 ]; then
        HEALTH="$((100 * FULL / DESIGN))%"
    fi
fi

VOLTAGE=$(cat /sys/class/power_supply/$BAT/voltage_now)
CURRENT=$(cat /sys/class/power_supply/$BAT/current_now)
TECHNOLOGY=$(cat /sys/class/power_supply/$BAT/technology)

MESSAGE="🔋 Capacidade: ${CAPACITY}%\n⚡ Status: ${STATUS}\n🩺 Saúde: ${HEALTH}\n🔌 Voltagem: $((VOLTAGE / 1000000))V\n🔋 Corrente: $((CURRENT / 1000000))A\n⚙️ Tecnologia: ${TECHNOLOGY}"

echo -e "$MESSAGE" | rofi -dmenu -p "Bateria" -theme-str "
window {
    width: 28ch;
    padding: 3px;
    background: '${background}';
}
mainbox {
    padding: 10px;
}
inputbar {
    enabled: false;
    visible: false;
}
listview {
    lines: 6;
    spacing: 7px;
    scrollbar: false;
    border: 0;
}
element {
    border: 0;
}
" 
