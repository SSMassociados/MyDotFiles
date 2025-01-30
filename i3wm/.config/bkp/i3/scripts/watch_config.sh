#!/bin/bash
CONFIG_FILE="$HOME/.config/i3/config"

# Loop infinito para manter a monitoração ativa
while true; do
    # Monitora o arquivo e reinicia o i3wm se houver mudanças
    inotifywait -e close_write "$CONFIG_FILE"
    i3-msg reload
    i3-msg restart
done
