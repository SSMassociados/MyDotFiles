#!/bin/bash

SOUND_OPEN=/usr/share/sounds/freedesktop/stereo/dialog-error.oga
SOUND_CLOSE=/usr/share/sounds/freedesktop/stereo/complete.oga

if ! command -v i3-msg &> /dev/null; then
    echo "Erro: i3-msg não encontrado. Instale o i3-msg para prosseguir." | tee -a ~/scripts_debug.log
    exit 1
fi

i3-msg -t subscribe '[ "window::new", "window::close" ]' | while read -r event; do
    echo "$(date) - Evento: $event" >> ~/scripts_debug.log  # Registro dos eventos para depuração
    if echo "$event" | grep -q '"change":"new"'; then
        paplay "$SOUND_OPEN" &
    elif echo "$event" | grep -q '"change":"close"'; then
        paplay "$SOUND_CLOSE" &
    fi
done
