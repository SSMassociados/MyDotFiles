#!/bin/bash

# Verifica se o NetworkManager está instalado e ativo
if ! command -v nmcli &> /dev/null; then
    notify-send "Erro" "NetworkManager (nmcli) não está instalado."
    exit 1
fi

# Obtém a conexão Wi-Fi ativa
ACTIVE_SSID=$(nmcli -t -f active,ssid dev wifi | grep '^sim' | cut -d':' -f2)

if [ -z "$ACTIVE_SSID" ]; then
    notify-send "Erro" "Nenhuma rede Wi-Fi conectada."
    exit 1
fi

# Obtém o arquivo de conexão no NetworkManager
CONNECTION_FILE=$(grep -l "ssid=$ACTIVE_SSID" /etc/NetworkManager/system-connections/*.nmconnection)

if [ -z "$CONNECTION_FILE" ]; then
    notify-send "Erro" "Arquivo de conexão não encontrado para: $ACTIVE_SSID"
    exit 1
fi

# Extrai a senha (supondo WPA/WPA2)
WIFI_PASSWORD=$(sudo grep -oP 'psk=\K.*' "$CONNECTION_FILE" 2>/dev/null)

if [ -z "$WIFI_PASSWORD" ]; then
    notify-send "Erro" "Senha não encontrada para: $ACTIVE_SSID"
    exit 1
fi

# Gera o QR Code no terminal (ANSI)
echo "🔵 Rede: $ACTIVE_SSID | Senha: $WIFI_PASSWORD"
echo "📡 QR Code para conexão:"
qrencode -t ANSIUTF8 "WIFI:S:$ACTIVE_SSID;T:WPA;P:$WIFI_PASSWORD;;"

# Opcional: Gerar também uma imagem PNG
QR_PNG="$HOME/wifi_$ACTIVE_SSID.png"
qrencode -o "$QR_PNG" "WIFI:S:$ACTIVE_SSID;T:WPA;P:$WIFI_PASSWORD;;"
notify-send "QR Code Gerado" "Salvo em: $QR_PNG"
