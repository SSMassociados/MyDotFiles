#!/bin/bash
# Versão com cache de alta velocidade
cache_file="/tmp/polybar_brightness_cache"

# Força atualização se receber argumento --update
if [ "$1" == "--update" ]; then
    ddcutil --brief getvcp 10 | awk '{print $4 "%"}' > "$cache_file"
fi

# Mostra valor cacheado ou atualiza se vazio
[ -s "$cache_file" ] && cat "$cache_file" || {
    current=$(ddcutil --brief getvcp 10 2>/dev/null | awk '{print $4 "%"}')
    echo "${current:---%}" > "$cache_file"
    cat "$cache_file"
}
