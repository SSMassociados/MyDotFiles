#!/bin/bash

while true; do
    # Obter informações sobre a bateria
    battery_info=$(upower -i /org/freedesktop/UPower/devices/battery_BAT0)
    
    # Extrair o nível de carga da bateria
    battery_level=$(echo "$battery_info" | grep -E "percentage" | awk '{print $2}' | tr -d '%')
    
    # Verificar se o carregador está conectado
    if [ "$(echo "$battery_info" | grep -c "state: *charging")" -eq 1 ]; then
        # Se o carregador estiver conectado e o nível da bateria for superior a 95%, emitir notificação
        if [ "$battery_level" -ge 95 ]; then
            notify-send "Desconecte o carregador" "A carga da bateria está acima de 95%."
            paplay /usr/share/sounds/freedesktop/stereo/complete.oga
        fi
    else
        # Se o carregador não estiver conectado e o nível da bateria for menor ou igual a 20%, emitir alerta
        if [ "$battery_level" -le 20 ]; then
            notify-send "Conecte o carregador" "A carga da bateria está abaixo de 20%."
            paplay /usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga
        fi
    fi
    
    # Aguardar 10 segundos antes de verificar novamente
    sleep 10
done
