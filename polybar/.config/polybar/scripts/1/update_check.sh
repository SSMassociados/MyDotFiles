#!/usr/bin/env bash

echo -e "\033[1;34m==> Pacotes Oficiais:\033[0m"
checkupdates
echo -e "\n\033[1;34m==> Pacotes AUR:\033[0m"
yay -Qum

# INTERAÇÃO PARA MANTER O TERMINAL ABERTO
echo -e "\n\033[1;32mPressione Enter para sair...\033[0m"
read -r
