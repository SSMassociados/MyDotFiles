#!/bin/bash

# Tempo de espera (em segundos) para repetir o aviso caso você ignore
# Ajustar o tempo de insistência para ser mais rápido ou mais demorado no futuro, 
# basta alterar o valor de: TEMPO_REPETICAO=300 segundos = 5 minutos
TEMPO_REPETICAO=100

ultimo_alerta_alto=0
ultimo_alerta_baixo=0

while true; do
    battery_info=$(upower -i /org/freedesktop/UPower/devices/battery_BAT0)

    if [ -n "$battery_info" ]; then
        battery_level=$(echo "$battery_info" | grep -E "percentage" | awk '{print $2}' | tr -d '%')
        is_charging=$(echo "$battery_info" | grep -c "state: *charging")
        agora=$(date +%s)

        # --- CENÁRIO 1: CARREGADOR CONECTADO (Acima de 95%) ---
        if [ "$is_charging" -eq 1 ]; then
            ultimo_alerta_baixo=0 # Reseta o timer do alerta baixo

            if [ "$battery_level" -ge 95 ]; then
                # Se nunca alertou OU se já passaram 5 minutos desde o último alerta
                if [ $ultimo_alerta_alto -eq 0 ] || [ $((agora - ultimo_alerta_alto)) -ge $TEMPO_REPETICAO ]; then
                    notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-90-charging-symbolic.svg "Desconecte o carregador" "A bateria está em ${battery_level}% e continua subindo!"
                    paplay "$HOME/.config/i3/sounds/95_remova.mp3"
                    ultimo_alerta_alto=$agora
                fi
            else
                ultimo_alerta_alto=0
            fi

        # --- CENÁRIO 2: NA BATERIA (Abaixo de 20%) ---
        else
            ultimo_alerta_alto=0 # Reseta o timer do alerta alto

            if [ "$battery_level" -le 20 ]; then
                # Se nunca alertou OU se já passaram 5 minutos desde o último alerta
                if [ $ultimo_alerta_baixo -eq 0 ] || [ $((agora - ultimo_alerta_baixo)) -ge $TEMPO_REPETICAO ]; then
                    notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-20-symbolic.svg "Conecte o carregador" "Bateria crítica em ${battery_level}%! Conecte a tomada."
                    paplay "$HOME/.config/i3/sounds/20_conectar.mp3"
                    ultimo_alerta_baixo=$agora
                fi
            else
                ultimo_alerta_baixo=0
            fi
        fi
    fi

    # Checa o status a cada 30 segundos
    sleep 30
done


##!/bin/bash

#while true; do
    ## Obter informações sobre a bateria
    #battery_info=$(upower -i /org/freedesktop/UPower/devices/battery_BAT0)

    ## Verificar se a obtenção das informações da bateria foi bem-sucedida
    #if [ -n "$battery_info" ]; then
        ## Extrair o nível de carga da bateria
        #battery_level=$(echo "$battery_info" | grep -E "percentage" | awk '{print $2}' | tr -d '%')

        ## Verificar se o carregador está conectado
        #if [ "$(echo "$battery_info" | grep -c "state: *charging")" -eq 1 ]; then
            ## Se o carregador estiver conectado e o nível da bateria for superior a 95%, emitir notificação
            #if [ "$battery_level" -ge 95 ]; then
                #notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-90-charging-symbolic.svg "Desconecte o carregador" "A carga da bateria está acima de 95%."
                ##paplay /usr/share/sounds/ocean/stereo/bell-window-system.oga
                #paplay "$HOME/.config/i3/sounds/95_remova.mp3"
            #fi
        #else
            ## Se o carregador não estiver conectado e o nível da bateria for menor ou igual a 20%, emitir alerta
            #if [ "$battery_level" -le 20 ]; then
                #notify-send --urgency=critical --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-20-symbolic.svg "Conecte o carregador" "A carga da bateria está abaixo de 20%."
                ##paplay /usr/share/sounds/enchanted/stereo/battery-low.ogg
                ##paplay /usr/share/sounds/harmony2/stereo/battery-low.ogg
                #paplay "$HOME/.config/i3/sounds/20_conectar.mp3"
            #fi
        #fi
    #else
        #echo "Erro ao obter informações da bateria."
    #fi

    ## Aguardar 10 segundos antes de verificar novamente
    #sleep 10
#done

