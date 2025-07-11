#!/bin/bash

# Encerra instâncias anteriores
killall -q picom

# Espera um pouco para garantir que finalizou
sleep 0.5

# Inicia o Picom em modo daemon com configuração personalizada
picom --config ~/.config/picom/picom.conf --daemon
