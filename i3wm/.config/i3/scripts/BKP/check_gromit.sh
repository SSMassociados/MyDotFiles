#!/bin/bash

# Verifica se o Gromit-MPX está em execução
if pgrep -x "gromit-mpx" > /dev/null
then
    echo "Gromit-MPX está em execução."
    
    # Verifica se o Picom está em execução
    if pgrep -x "picom" > /dev/null
    then
        echo "Picom está em execução. Encerrando o Picom..."
        killall picom
    else
        echo "Picom não está em execução."
    fi
else
    echo "Gromit-MPX não está em execução."
fi
