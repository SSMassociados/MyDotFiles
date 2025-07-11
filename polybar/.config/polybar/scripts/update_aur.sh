#!/bin/bash

# Atualiza o AUR
yay -Sua --noconfirm && notify-send -t 5000 "✅ Atualização AUR concluída!"

# Aguarda para o usuário ver a notificação
sleep 5
i3-msg restart

# Atualiza o módulo na Polybar
# polybar-msg action "#sys_updates.hook.0"

# Fecha o terminal
#exit

sleep 1 && \
kill -TERM $PPID

#echo -e "\n\033[1;32mPressione Enter para sair...\033[0m"
#read -r  # Mantém o terminal aberto até o usuário pressionar Enter


