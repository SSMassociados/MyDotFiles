#!/bin/bash

# Caminho para o arquivo de cores gerado pelo wal
WAL_COLORS_FILE=~/.cache/wal/colors.json

# Verifica se o arquivo de cores existe
if [[ ! -f $WAL_COLORS_FILE ]]; then
    echo "Erro: Arquivo $WAL_COLORS_FILE não encontrado!"
    exit 1
fi

# Função para converter hexadecimal em RGB
hex_to_rgb() {
    local hex=${1#"#"}
    echo "$((16#${hex:0:2})) $((16#${hex:2:2})) $((16#${hex:4:2}))"
}

# Função para calcular a luminância relativa
calculate_luminance() {
    local r g b
    read r g b <<< $(hex_to_rgb "$1")
    r=$(awk "BEGIN {print ($r / 255) < 0.03928 ? ($r / 255) / 12.92 : ((($r / 255) + 0.055) / 1.055)^2.4}")
    g=$(awk "BEGIN {print ($g / 255) < 0.03928 ? ($g / 255) / 12.92 : ((($g / 255) + 0.055) / 1.055)^2.4}")
    b=$(awk "BEGIN {print ($b / 255) < 0.03928 ? ($b / 255) / 12.92 : ((($b / 255) + 0.055) / 1.055)^2.4}")
    awk "BEGIN {print 0.2126 * $r + 0.7152 * $g + 0.0722 * $b}"
}

# Função para ajustar a cor da fonte com base no contraste
adjust_text_color() {
    local bg_color="$1"
    local text_light="#FFFFFF"
    local text_dark="#000000"

    local bg_luminance=$(calculate_luminance "$bg_color")
    local light_luminance=$(calculate_luminance "$text_light")
    local dark_luminance=$(calculate_luminance "$text_dark")

    local contrast_with_light=$(awk "BEGIN {print ($light_luminance + 0.05) / ($bg_luminance + 0.05)}")
    local contrast_with_dark=$(awk "BEGIN {print ($bg_luminance + 0.05) / ($dark_luminance + 0.05)}")

    if (( $(echo "$contrast_with_light > $contrast_with_dark" | bc -l) )); then
        echo "$text_light"
    else
        echo "$text_dark"
    fi
}

# Extraímos as cores do arquivo JSON
BG_COLOR=$(jq -r '.colors.color2' "$WAL_COLORS_FILE")
TEXT_COLOR=$(adjust_text_color "$BG_COLOR")
INACTIVE_BG_COLOR=$(jq -r '.colors.color0' "$WAL_COLORS_FILE")
INACTIVE_TEXT_COLOR=$(adjust_text_color "$INACTIVE_BG_COLOR")
URGENT_BG_COLOR=$(jq -r '.colors.color1' "$WAL_COLORS_FILE")
FRAME_COLOR="$BG_COLOR"  # Usando a cor de fundo como frame color

# Debug: Verifique se as cores foram extraídas corretamente (ativar com --debug)
if [[ "$1" == "--debug" ]]; then
    echo "BG_COLOR=$BG_COLOR"
    echo "TEXT_COLOR=$TEXT_COLOR"
    echo "INACTIVE_BG_COLOR=$INACTIVE_BG_COLOR"
    echo "INACTIVE_TEXT_COLOR=$INACTIVE_TEXT_COLOR"
    echo "URGENT_BG_COLOR=$URGENT_BG_COLOR"
    echo "FRAME_COLOR=$FRAME_COLOR"
fi

# Caminho do template e do arquivo de saída do dunst
DUNST_TEMPLATE=~/.config/dunst/dunstrc.template
DUNST_OUTPUT=~/.config/dunst/dunstrc

# Substituir as cores no template do dunst
sed -e "s/{bg-color}/$BG_COLOR/g" \
    -e "s/{text-color}/$TEXT_COLOR/g" \
    -e "s/{inactive-bg-color}/$INACTIVE_BG_COLOR/g" \
    -e "s/{inactive-text-color}/$INACTIVE_TEXT_COLOR/g" \
    -e "s/{urgent-bg-color}/$URGENT_BG_COLOR/g" \
    -e "s/{frame-color}/$FRAME_COLOR/g" \
    "$DUNST_TEMPLATE" > "$DUNST_OUTPUT"

# Verifica se ainda existem placeholders não substituídos
if grep -q '{.*}' "$DUNST_OUTPUT"; then
    echo "Aviso: Nem todos os placeholders foram substituídos no $DUNST_OUTPUT"
fi

# Reiniciar o Dunst para aplicar as mudanças
if pgrep dunst > /dev/null; then
    killall dunst
fi
dunst --config "$DUNST_OUTPUT" &
