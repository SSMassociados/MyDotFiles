#!/bin/bash

# Detecta bateria automaticamente
battery=$(ls /sys/class/power_supply/ | grep -i '^BAT')

# Verifica se encontrou bateria
if [ -z "$battery" ]; then
    echo "🔋 N/A"
    exit 0
fi

# Caminho base (CORRIGIDO)
path="/sys/class/power_supply/$battery"

# Verifica se arquivos necessários existem
if [ ! -f "$path/capacity" ]; then
    echo "🔋 N/A"
    exit 0
fi

# Pega os dados básicos
status=$(cat "$path/status" 2>/dev/null)
capacity=$(cat "$path/capacity" 2>/dev/null)

# Ícone para status
case $status in
    Charging) icon="⚡";;
    Discharging) icon="🔋";;
    Full) icon="✅";;
    Unknown) icon="❓";;
    *) icon="❓";;
esac

# Exibe apenas ícone e porcentagem para o Polybar
echo "$icon $capacity%"
