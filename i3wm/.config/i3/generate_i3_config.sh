#!/bin/bash

# Carregue as cores geradas pelo wal
source ~/.cache/wal/colors.sh

# Crie o arquivo de configuração do i3 com as cores do wal
sed -e "s/%color1%/$color1/g" \
    -e "s/%color2%/$color2/g" \
    -e "s/%color3%/$color3/g" \
    -e "s/%color4%/$color4/g" \
    -e "s/%color5%/$color5/g" \
    -e "s/%color6%/$color6/g" \
    -e "s/%color7%/$color7/g" \
    -e "s/%color8%/$color8/g" \
    -e "s/%color9%/$color9/g" \
    -e "s/%color10%/$color10/g" \
    -e "s/%color11%/$color11/g" \
    -e "s/%color12%/$color12/g" \
    -e "s/%color13%/$color13/g" \
    -e "s/%color14%/$color14/g" \
    -e "s/%color15%/$color15/g" \
    -e "s/%color16%/$color16/g" \
    -e "s/%color17%/$color17/g" \
    -e "s/%color18%/$color18/g" \
    -e "s/%color19%/$color19/g" \
    -e "s/%color20%/$color20/g" \
    ~/.config/i3/config.template > ~/.config/i3/config
