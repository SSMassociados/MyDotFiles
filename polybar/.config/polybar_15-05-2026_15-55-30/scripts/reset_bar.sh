#!/usr/bin/env bash

# Termina instâncias existentes
killall -q polybar

# Aguarda o término
while pgrep -f polybar >/dev/null; do sleep 1; done

# Lança a Polybar em cada monitor detectado
if type "xrandr" > /dev/null; then
  for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    MONITOR=$m polybar --reload main &
  done
else
  polybar --reload main &
fi

# Aguarda estabilização
sleep 1

# Reinicia apps de Systray
if [[ -n "${SYSTRAY_APPS[*]}" ]]; then
  for app in "${SYSTRAY_APPS[@]}"; do
    if command -v "$app" > /dev/null; then
      echo " - Iniciando $app &"
      "$app" &
      sleep 0.5
    fi
  done
fi

# Notificação de sucesso com stack-tag
if command -v notify-send > /dev/null; then
  notify-send -h string:x-dunst-stack-tag:polybar-reload "Polybar" "Reiniciada com sucesso! 🎉"
fi

echo "Polybar reiniciada com sucesso."
