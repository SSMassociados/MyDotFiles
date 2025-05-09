#!/bin/bash

# Carrega as cores do Pywal
source "${HOME}/.cache/wal/colors.sh"

# Define cores com fallback
fg="${color7:-#f3f4f5}"       # Texto principal
bg="${color0:-#2E3440}"       # Fundo principal
frame="${color15:-#D8DEE9}"   # Borda/destaque

# Gera log de debug
{
    echo "==== alttab iniciado ===="
    echo "FG    (texto):  $fg"
    echo "BG    (fundo):  $bg"
    echo "Frame (borda):  $frame"
    echo "Wallpaper atual: $wallpaper"
    echo "Data/Hora: $(date)"
} >> /tmp/alttab_debug.log

# Encerra instância anterior
killall alttab 2>/dev/null

# Inicia o alttab com parâmetros personalizados
alttab -pk h -nk l \
  -fg "$fg" \
  -bg "$bg" \
  -frame "$frame" \
  -t 80x80 \
  -i 64x64 \
  -p center \
  -bw 1 &

# Salva status do comando
echo "Status do alttab: $?" >> /tmp/alttab_debug.log
