#!/bin/bash

# Escolhe wallpaper aleatório para o betterlockscreen
wallpaper_path=$(find -L ~/.wallpaper -type f \( -name '*.jpg' -o -name '*.png' \) | shuf -n 1)
betterlockscreen -u "$wallpaper_path"

# Mata swayidle antigo, se existir
pkill -x swayidle 2>/dev/null

# Inicia swayidle
swayidle -w \
    timeout 120 "betterlockscreen -l dim" \
    timeout 210 "systemctl suspend" \
    resume 'xset dpms force on'
