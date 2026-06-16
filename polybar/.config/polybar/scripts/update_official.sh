#!/usr/bin/env bash
set -u
IFS=$'\n\t'

# Verifica atualizações do repositório oficial
repo_updates=$(checkupdates 2>/dev/null | wc -l) || repo_updates=0

if (( repo_updates > 0 )); then
    if sudo pacman -Syu --noconfirm; then
        notify-send -t 5000 "✅ Atualização Oficial Concluída!"
        polybar-msg action "#sys_updates.module-reload" 2>/dev/null || true
    else
        notify-send -t 5000 "❌ Falha na atualização oficial!"
    fi
else
    notify-send -t 3000 "Nenhuma atualização oficial disponível."
fi

xdo raise -N Polybar

# Interação para manter o terminal aberto
echo -e "\n\033[1;32mPressione Enter para sair...\033[0m"
read -r
