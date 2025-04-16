#!/bin/bash

while true; do
    # Obter informações sobre a bateria
    battery_info=$(upower -i /org/freedesktop/UPower/devices/battery_BAT0)

    # Verificar se a obtenção das informações da bateria foi bem-sucedida
    if [ -n "$battery_info" ]; then
        # Extrair o nível de carga da bateria
        battery_level=$(echo "$battery_info" | grep -E "percentage" | awk '{print $2}' | tr -d '%')

        # Verificar se o carregador está conectado
        if [ "$(echo "$battery_info" | grep -c "state: *charging")" -eq 1 ]; then
            # Se o carregador estiver conectado e o nível da bateria for superior a 95%, emitir notificação
            if [ "$battery_level" -ge 95 ]; then
                notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-90-charging-symbolic.svg "Desconecte o carregador" "A carga da bateria está acima de 95%."
                paplay /usr/share/sounds/ocean/stereo/bell-window-system.oga
            fi
        else
            # Se o carregador não estiver conectado e o nível da bateria for menor ou igual a 20%, emitir alerta
            if [ "$battery_level" -le 20 ]; then
                notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-20-symbolic.svg "Conecte o carregador" "A carga da bateria está abaixo de 20%."
                paplay /usr/share/sounds/enchanted/stereo/battery-low.ogg
            fi
        fi
    else
        echo "Erro ao obter informações da bateria."
    fi

    # Aguardar 10 segundos antes de verificar novamente
    sleep 10
done
