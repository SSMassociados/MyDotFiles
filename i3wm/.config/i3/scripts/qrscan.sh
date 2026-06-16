#!/usr/bin/env bash
# qrscan.sh
# Dependencies: flameshot, zbar, xclip
# yay -S flameshot zbar xclip

screenshot="/tmp/zbar_screenshot.png"

flameshot gui -p "$screenshot"

if [ ! -f "$screenshot" ]; then
    echo "Erro: screenshot não foi criado (captura cancelada?)"
    exit 1
fi

if zbarimg -q --raw "$screenshot" | xclip -selection clipboard; then
    rm -f "$screenshot"
    exit 0
else
    echo "Erro: nenhum QR Code encontrado ou falha ao copiar"
    rm -f "$screenshot"
    exit 1
fi
