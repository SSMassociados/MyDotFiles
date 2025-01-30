#!/bin/bash

# Função para exibir notificação usando Dunst
show_notification() {
    dunstify -i /caminho/para/icone.png "Picom" "$1"
}

# Verifica se o Picom está em execução
if pgrep -x "picom" > /dev/null
then
    # Se estiver em execução, mata o processo
    pkill picom
    show_notification "Picom Desativado."
else
    # Se não estiver em execução, inicia o Picom
    picom --config ~/.config/picom/picom.conf &
    show_notification "Picom Ativado."
fi




