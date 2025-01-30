#!/bin/bash

# Define os horários de notificação
horarios=("07:29" "08:19" "09:09" "09:29" "10:19" "11:09" "11:59" "12:59" "13:49" "14:39")

# Loop infinito para verificar a hora atual
while true; do
    # Obtém o dia da semana (1 a 7, onde 1 é segunda-feira)
    dia_semana=$(date +%u)

    # Verifica se é um dia de semana (segunda-feira a sexta-feira, 1 a 5)
    if [ "$dia_semana" -ge 1 ] && [ "$dia_semana" -le 5 ]; then
        # Obtém a hora atual
        hora_atual=$(date +%H:%M)

        # Verifica se a hora atual corresponde a algum horário de notificação
        for horario in "${horarios[@]}"; do
            if [ "$hora_atual" == "$horario" ]; then
                # Notificação visual
                notify-send -u critical -i /usr/share/icons/gnome/256x256/status/appointment-soon.png "Hora de tocar a campainha!" "Hora atual: $hora_atual"

                # Som de notificação
                paplay /usr/share/sounds/freedesktop/stereo/alarm.mp3

                # Aguarda 10 segundos antes de verificar novamente (evita notificações múltiplas no mesmo horário)
                sleep 10
            fi
        done
    fi

   # Aguarda 10 segundos antes de verificar a hora novamente
    sleep 10
done
