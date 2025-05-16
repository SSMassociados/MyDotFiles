#!/bin/bash

export DISPLAY=:0

BAT="BAT0"
CAPACITY=$(tr -d '\n' < /sys/class/power_supply/$BAT/capacity)
STATUS=$(tr -d '\n' < /sys/class/power_supply/$BAT/status)

HEALTH="N/A"
if [ -f /sys/class/power_supply/$BAT/charge_full_design ]; then
    FULL=$(tr -d '\n' < /sys/class/power_supply/$BAT/charge_full)
    DESIGN=$(tr -d '\n' < /sys/class/power_supply/$BAT/charge_full_design)
    if [ "$DESIGN" -gt 0 ]; then
        HEALTH="$((100 * FULL / DESIGN))%"
    fi
fi

echo "🔋 ${CAPACITY}% | ⚡ ${STATUS} | 🩺 ${HEALTH}" | \
rofi -dmenu -filter " " \
-theme-str '
window {
    width: 38ch;
    padding: 5px;
}
inputbar {
    enabled: false;
    visible: false;
    children: [];
    margin: 0;
    padding: 0;
    border: 0;
}
listview {
    lines: 1;
    scrollbar: false;
    border: 0;
    padding: 0;
}
element {
    border: 0;
}
'
