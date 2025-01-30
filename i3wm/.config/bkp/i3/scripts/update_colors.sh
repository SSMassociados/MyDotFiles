#!/bin/bash
wal -i ~/.wallpaper --iterative
~/.config/i3/scripts/generate_colors_i3.sh
i3-msg reload
