#!/bin/bash
if pgrep yad >/dev/null 2>&1; then
    pkill yad
else
    yad --title='Calendar' --calendar --no-buttons --undecorated --posx=1020 --posy=30 &
fi
