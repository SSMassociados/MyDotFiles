#!/bin/bash

while true; do
    # Espera por mudanças no sistema de DRM (monitores)
    inotifywait -q -e change /sys/class/drm/*/status

    # Aplica a configuração (igual ao script anterior)
    if [ $(mons -m | wc -l) -gt 2 ]; then
        mons -e right
    else
        mons -o
    fi
done
