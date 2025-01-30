#!/bin/bash

# Verifique se o utilitário system-config-printer está em execução
if pgrep -f "system-config-printer" > /dev/null
then
    # Se estiver em execução, encerre-o
    pkill -f "system-config-printer"
else
    # Se não estiver em execução, inicie-o apenas se não houver outro processo em execução
    if ! pgrep -f "system-config-printer" > /dev/null
    then
        system-config-printer &
    fi
fi
