#!/bin/bash

get_cpu_temp() {
    local sensors_output=$(sensors 2>/dev/null)
    # Correção do sinal de + escapado (\+)
    local pkg_temp=$(echo "$sensors_output" | awk '
        /Package id 0/ || /Core 0/ {
            for(i=1; i<=NF; i++) {
                if($i ~ /\+[0-9]+\.[0-9]°C/) {
                    gsub(/[+°C]/, "", $i)
                    print $i
                    exit
                }
            }
        }
    ')

    if [[ "$pkg_temp" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "$pkg_temp"
    else
        # Fallback térmico simplificado
        find /sys/class/thermal/thermal_zone* -type f -exec cat {} + 2>/dev/null | 
        awk '{t=$1/1000; if(t>max) max=t} END {printf "%.1f", max}'
    fi
}

temp=$(get_cpu_temp)

# Cores e Ícones
if (( $(echo "$temp >= 80" | bc -l) )); then
    echo "%{F#ef02db} ${temp}°C%{F-}"
elif (( $(echo "$temp >= 65" | bc -l) )); then
    echo "%{F#ff3205} ${temp}°C%{F-}"
elif (( $(echo "$temp >= 45" | bc -l) )); then
    echo "%{F#f4cb24} ${temp}°C%{F-}"
else
    echo "%{F#6bff49} ${temp}°C%{F-}"
fi
