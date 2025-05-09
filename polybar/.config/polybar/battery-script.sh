#!/bin/bash

# Dados da bateria
BAT="BAT0"
CAPACITY=$(cat /sys/class/power_supply/$BAT/capacity)
STATUS=$(cat /sys/class/power_supply/$BAT/status)

# Saúde da bateria (se disponível)
HEALTH="N/A"
[ -f /sys/class/power_supply/$BAT/charge_full_design ] && {
    FULL=$(cat /sys/class/power_supply/$BAT/charge_full)
    DESIGN=$(cat /sys/class/power_supply/$BAT/charge_full_design)
    [ $DESIGN -gt 0 ] && HEALTH="$((100 * FULL / DESIGN))%"
}

# Exibição formatada
echo "┌───────────────┐"
printf "│ %-13s │\n" "🔋 $CAPACITY%"
printf "│ %-13s │\n" "⚡ $STATUS"
printf "│ %-13s │\n" "🩺 $HEALTH"
echo "└───────────────┘"
