#!/usr/bin/env bash
set -u
IFS=$'\n\t'

# Verifica atualizações do AUR com tratamento de erro
aur_updates=$(yay -Qum 2>/dev/null | wc -l) || aur_updates=0

if (( aur_updates > 0 )); then
    if yay -Sua --noconfirm; then
        notify-send -t 5000 "✅ Atualização AUR concluída!"
        polybar-msg cmd restart
    else
        notify-send -t 5000 "❌ Falha na atualização do AUR!"
    fi
else
    notify-send -t 3000 "Nenhuma atualização AUR disponível."
fi

# Interação para manter o terminal aberto
echo -e "\n\033[1;32mPressione Enter para sair...\033[0m"
read -r

