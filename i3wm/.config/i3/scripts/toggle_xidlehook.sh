#!/bin/bash

# Função para exibir notificação usando Dunst
show_notification() {
    dunstify -i /caminho/para/icone.png "xidlehook" "$1"
}

# Verifica se o xidlehook está em execução
if pgrep -x "xidlehook" > /dev/null
then
    # Se estiver em execução, mata o processo
    pkill xidlehook
    show_notification "Xidlehook Desativado."
else
    # Se não estiver em execução, inicia o xidlehook
    xidlehook &
    show_notification "Xidlehook Ativado."
fi
