#!/bin/bash

while true; do
  # Verifica se o gromit-mpx está sendo executado
  if pgrep -x "gromit-mpx" > /dev/null; then
    # Desabilita o picom se ele estiver ativo
    if pgrep -x "picom" > /dev/null; then
      pkill picom
    fi
  fi

  # Aguarda 10 segundos antes de verificar novamente
  sleep 10
done
