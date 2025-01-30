#!/bin/bash

# Verifica se o Dunst está em execução
if pgrep -x "dunst" > /dev/null
then
    # Se estiver em execução, mata o processo
    pkill dunst
else
    # Se não estiver em execução, inicia o Dunst
    dunst -b &
fi
