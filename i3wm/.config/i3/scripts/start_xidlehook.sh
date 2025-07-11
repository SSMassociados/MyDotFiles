#!/bin/bash

wallpaper_path=$(find -L ~/.wallpaper -type f \( -name '*.jpg' -o -name '*.png' \) | shuf -n 1)

# Não ativa quando um aplicativo está em tela cheia
# Não ativa quando o áudio está sendo reproduzido
# Primeiro temporizador: 120s de inatividade → bloquear tela
# Segundo temporizador: 90s depois disso → suspender sistema
# Opções: -l (blur color dim dimblur dimpixel pixel resize)

xidlehook \
  --not-when-fullscreen \
  --not-when-audio \
  --timer 120 "betterlockscreen -u '$wallpaper_path' -l dim" "" \
  --timer 90 "systemctl suspend" ""
  
# Checar se estar executando? 
# ps aux | grep xidlehook
# pgrep -fl "xidlehook --not-when-fullscreen --not-when-audio"

