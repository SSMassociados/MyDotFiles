#!/bin/bash
if pgrep -f "watch sensors"; then
    pkill -f "watch sensors"
else
    watch sensors
fi



