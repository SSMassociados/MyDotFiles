#!/bin/bash
# Configurações do YAD
YAD_OPTIONS="--calendar --title='Calendar' --no-buttons --undecorated --borders=0 --skip-taskbar --on-top --mouse"
YAD_STYLE="--gtk-palette=bg:#1e1e1e,fg:#ffffff,sel:#ff3b30 --opacity=0.95"
FONT_OPTION="--font=SF Pro Display Bold 11"
#YAD_POSITION="--posx=3080 --posy=47"
YAD_POSITION="--posx=1040 --posy=30"

# Verifica pelo título exato "Calendar"
if pgrep -f "yad.*--title='Calendar'" >/dev/null; then
    pkill -f "yad.*--title='Calendar'"
else
    # Lança novo calendário
    yad $YAD_OPTIONS $YAD_STYLE $FONT_OPTION $YAD_POSITION &
fi
