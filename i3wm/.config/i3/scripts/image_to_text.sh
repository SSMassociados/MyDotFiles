#!/usr/bin/env bash
# Dependencies: flameshot, xclip, tesseract, tesseract-data-best-por, imagemagick
# yay -S flameshot xclip tesseract tesseract-data-best-por imagemagick

screenshot="/tmp/tesseract_screenshot.png"
preprocessed="/tmp/tesseract_preprocessed.png"
output="/tmp/tesseract_output"

flameshot gui -p "$screenshot"

if [ ! -f "$screenshot" ]; then
    echo "Erro: screenshot não foi criado (captura cancelada?)"
    exit 1
fi

convert "$screenshot" -resize 300% -colorspace Gray -threshold 50% "$preprocessed"

if LANG=pt_BR.UTF-8 tesseract "$preprocessed" "$output" -l por --psm 6; then
    cat "${output}.txt" | xclip -selection clipboard
    rm -f "$screenshot" "$preprocessed" "${output}.txt"
    exit 0
else
    echo "Erro: falha no OCR"
    rm -f "$screenshot" "$preprocessed" "${output}.txt"
    exit 1
fi
