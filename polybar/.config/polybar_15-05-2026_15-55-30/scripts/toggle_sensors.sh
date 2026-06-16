#!/bin/bash

if xdotool search --name "sensors" 2>/dev/null | grep -q .; then
    i3-msg '[title="sensors"]' focus
else
    kitty -T sensors watch sensors &
    sleep 1
    i3-msg '[title="sensors"]' fullscreen enable
fi
