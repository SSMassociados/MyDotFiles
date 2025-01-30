#!/bin/sh
# SPDX-License-Identifier: 0BSD
# dependencias: upower, ffplay ou paplay, notify-send, dbus

while true; do
    # Obtém o nível de carga da bateria e o estado atual da bateria usando o comando upower
    BATERIA=$(upower -i $(upower -e | grep 'BAT') | awk '/percentage/ { print $2 }' | uniq | cut -c1-2)
    ESTADO=$(upower -i $(upower -e | grep 'BAT') | awk '/state/ { print $2 }' | uniq)

    # Verifica se o nível de carga da bateria é maior ou igual a 95% e se a bateria está carregando
    if [ "$BATERIA" -ge 95 ] && [ "$ESTADO" = 'charging' ]; then
        # Toca um som de alerta e emite uma notificação informando que a bateria está carregada
        paplay /usr/share/sounds/freedesktop/stereo/bell.oga &&
        notify-send --urgency=critical \
        --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-90-charging-symbolic.svg \
        "Bateria carregada ${BATERIA}%" 'No talo'

    # Verifica se o nível de carga da bateria é menor que 20% e se a bateria está descarregando
    elif [ "$BATERIA" -lt 20 ] && [ "$ESTADO" = 'discharging' ]; then
        # Toca um som de alerta e emite uma notificação informando que a bateria está baixa
        paplay /usr/share/sounds/freedesktop/stereo/bell.oga &&
        notify-send --urgency=critical \
        --icon=/usr/share/icons/Adwaita/symbolic/status/battery-level-20-symbolic.svg \
        "Bateria baixa ${BATERIA}%" 'Descarregando'
    fi

    # Aguarda 10 segundos antes de verificar novamente o status da bateria
    sleep 10
done
