#!/bin/bash

# Detecta bateria automaticamente
battery=$(ls /sys/class/power_supply/ | grep -i '^BAT')

# Verifica se encontrou bateria
if [ -z "$battery" ]; then
    echo "🔋 Nenhuma bateria detectada"
    exit 0
fi

# Caminho base
path="/sys/class/power_supply/$battery"

# Verifica se arquivos necessários existem
if [ ! -f "$path/capacity" ]; then
    echo "🔋 Bateria não suporta leitura detalhada"
    exit 0
fi

# Pega os dados básicos
status=$(cat "$path/status" 2>/dev/null)
capacity=$(cat "$path/capacity" 2>/dev/null)

# Inicializa saúde como "N/A"
health="N/A"
cycles=""

# Verifica qual par de arquivos existe: charge_* ou energy_*
if [ -f "$path/charge_full_design" ] && [ -f "$path/charge_full" ]; then
    full=$(cat "$path/charge_full")
    design=$(cat "$path/charge_full_design")
    if [ "$design" -gt 0 ]; then
        health=$(( 100 * full / design ))%
    fi
elif [ -f "$path/energy_full_design" ] && [ -f "$path/energy_full" ]; then
    full=$(cat "$path/energy_full")
    design=$(cat "$path/energy_full_design")
    if [ "$design" -gt 0 ]; then
        health=$(( 100 * full / design ))%
    fi
fi

# Tenta pegar o número de ciclos, só exibe se for diferente de 0
if [ -f "$path/cycle_count" ]; then
    count=$(cat "$path/cycle_count")
    if [ "$count" -gt 0 ]; then
        cycles=" | Ciclos: $count"
    fi
fi

# Ícone para status
case $status in
    Charging) icon="⚡";;
    Discharging) icon="🔋";;
    Full) icon="✅";;
    Unknown) icon="❓";;
    *) icon="❓";;
esac

# Exibe resultado
echo "$icon $capacity% | Saúde: $health$cycles"
