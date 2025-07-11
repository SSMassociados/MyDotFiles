#!/bin/bash

# Atualiza o sistema
sudo pacman -Syu --noconfirm && notify-send -t 5000 "✅ Atualização Oficial Concluída!"

# Aguarda para o usuário ver a notificação
sleep 5
i3-msg restart

# Atualiza o módulo na Polybar
# polybar-msg action "#sys_updates.hook.0"

# Fecha o terminal
# exit

sleep 1 && \
kill -TERM $PPID
