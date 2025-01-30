#!/bin/bash

# Caminho para os arquivos de configuração
I3_CONFIG=~/.config/i3/config
DUNST_TEMPLATE=~/.config/dunst/dunstrc.template
DUNST_OUTPUT=~/.config/dunst/dunstrc

# Extrair cores do i3
BG_COLOR=$(grep 'set_from_resource \$bg-color' "$I3_CONFIG" | awk '{print $3}')
INACTIVE_BG_COLOR=$(grep 'set_from_resource \$inactive-bg-color' "$I3_CONFIG" | awk '{print $3}')
TEXT_COLOR=$(grep 'set_from_resource \$text-color' "$I3_CONFIG" | awk '{print $3}')
INACTIVE_TEXT_COLOR=$(grep 'set_from_resource \$inactive-text-color' "$I3_CONFIG" | awk '{print $3}')
URGENT_BG_COLOR=$(grep 'set_from_resource \$urgent-bg-color' "$I3_CONFIG" | awk '{print $3}')
FRAME_COLOR=$BG_COLOR  # Atualize para refletir o $bg-color do i3

# Substituir placeholders no template
sed -e "s/{bg-color}/$BG_COLOR/g" \
    -e "s/{inactive-bg-color}/$INACTIVE_BG_COLOR/g" \
    -e "s/{text-color}/$TEXT_COLOR/g" \
    -e "s/{inactive-text-color}/$INACTIVE_TEXT_COLOR/g" \
    -e "s/{urgent-bg-color}/$URGENT_BG_COLOR/g" \
    -e "s/{frame-color}/$FRAME_COLOR/g" \
    "$DUNST_TEMPLATE" > "$DUNST_OUTPUT"

# Reiniciar o Dunst para aplicar alterações
killall dunst && dunst &

