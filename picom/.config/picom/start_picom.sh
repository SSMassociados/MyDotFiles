#!/bin/sh
sleep 1  # Espera 1s para evitar conflitos

# Verifica se o Picom está rodando e mata se estiver
if pgrep -x "picom" > /dev/null; then
    pkill -9 picom
    sleep 0.5  # Tempo para garantir que o processo foi encerrado
fi

# Inicia o Picom com o arquivo de configuração
picom --config ~/.config/picom/picom.conf --daemon
