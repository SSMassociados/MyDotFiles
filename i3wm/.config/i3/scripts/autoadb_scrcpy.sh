#!/bin/bash

echo "Iniciando script de monitoramento de dispositivo..."

while true; do
  echo "Verificando dispositivos conectados..."

  # Verifica se há dispositivos conectados
  devices=$(adb devices | grep -w "device" | awk '{print $1}')

  if [ -n "$devices" ]; then
    echo "Dispositivo conectado: $devices"

    # Verifica se o scrcpy já está em execução
    if pgrep -x "scrcpy" > /dev/null; then
      echo "scrcpy já está em execução."
    else
      echo "Iniciando scrcpy..."
      scrcpy -MKSts $devices &
      echo "scrcpy iniciado com sucesso!"
    fi
  else
    echo "Nenhum dispositivo detectado. Tentando reconectar..."
    adb kill-server  # Encerra o servidor ADB
    adb start-server  # Inicia o servidor ADB
    adb reconnect offline  # Tenta reconectar dispositivos offline
  fi

  # Aguarda 2 segundos antes de verificar novamente
  sleep 2
done
