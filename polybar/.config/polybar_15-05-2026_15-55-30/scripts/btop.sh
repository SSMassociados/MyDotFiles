#!/bin/bash

if pgrep -x "btop" > /dev/null; then
    i3-msg '[title="btop"] focus'
else
    kitty -T btop btop &
    sleep 1
    i3-msg '[title="btop"] fullscreen enable'
fi
