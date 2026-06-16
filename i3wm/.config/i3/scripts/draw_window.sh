#!/usr/bin/env bash
# draw_window.sh
# Dependencies: slop, xdotool, xwininfo, wmctrl
# yay -S slop xdotool xwininfo wmctrl

geometry=$(slop -f '0,%x,%y,%w,%h') || exit 1

/usr/bin/kitty &
pid=$!

attempts=0
until id=$(xdotool search --pid "$pid" 2>/dev/null) && [ -n "$id" ]; do
    sleep 0.1
    (( attempts++ ))
    [ $attempts -ge 50 ] && { echo "Timeout: janela não encontrada"; exit 1; }
done

id=$(echo "$id" | tail -1)

attempts=0
until xwininfo -id "$id" 2>/dev/null | grep -q "IsViewable"; do
    sleep 0.1
    id=$(xdotool search --pid "$pid" 2>/dev/null | tail -1)
    (( attempts++ ))
    [ $attempts -ge 50 ] && { echo "Timeout: janela não visível"; exit 1; }
done

i3-msg "[id=$id]" floating enable, border none || { echo "Falha no i3-msg"; exit 1; }
wmctrl -i -r "$id" -e "$geometry"
