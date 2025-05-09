#!/bin/bash

# Função segura para obter temperatura da CPU
get_cpu_temp() {
    # 1. Tentar lm_sensors (Package ID para Intel)
    local sensors_output=$(sensors 2>/dev/null)
    local pkg_temp=$(echo "$sensors_output" | awk '
        /Package id 0/ {
            for(i=1; i<=NF; i++) {
                if($i ~ /+[0-9]+\.[0-9]°C/) {
                    gsub(/[+°C]/, "", $i)
                    print $i
                    exit
                }
            }
        }
    ')

    # 2. Tentar leitura direta do kernel (priorizando zonas CPU)
    local cpu_zone_temp=$(for zone in /sys/class/thermal/thermal_zone*; do
        if grep -q -E '(cpu|processor|core)' "$zone/type" 2>/dev/null; then
            awk '{printf "%.1f", $1/1000}' "$zone/temp" 2>/dev/null
        fi
    done | sort -nr | head -1)

    # 3. Fallback para qualquer zona térmica
    local any_zone_temp=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | 
                         awk '{t=$1/1000; if(t>max)max=t} END{printf "%.1f", max}')

    # Priorizar Package, depois zona CPU específica, depois qualquer zona
    if [[ "$pkg_temp" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$pkg_temp"
    elif [[ "$cpu_zone_temp" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$cpu_zone_temp"
    elif [[ "$any_zone_temp" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$any_zone_temp"
    else
        echo "0"
    fi
}

# Obter temperatura
temp=$(get_cpu_temp)

# Debug (opcional)
echo "Temperatura lida: $temp" > /tmp/cpu_temp_debug.log

# Validar
if ! [[ "$temp" =~ ^[0-9]+(\.[0-9]+)?$ ]] || (( $(echo "$temp == 100" | bc -l 2>/dev/null) )); then
    # Se for exatamente 100°C ou inválido, usar fallback
    temp=$(cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | 
          awk '{t=$1/1000; if(t>0 && t<100) print t}' | sort -nr | head -1)
    [[ -z "$temp" ]] && temp=0
fi

# Escala de cores
if (( $(echo "$temp >= 85" | bc -l 2>/dev/null) )); then
    echo "%{F#ef02db} ${temp}°C%{F-}"
elif (( $(echo "$temp >= 70" | bc -l 2>/dev/null) )); then
    echo "%{F#ff3205} ${temp}°C%{F-}"
elif (( $(echo "$temp >= 50" | bc -l 2>/dev/null) )); then
    echo "%{F#f4cb24} ${temp}°C%{F-}"
else
    echo "%{F#6bff49} ${temp}°C%{F-}"
fi
