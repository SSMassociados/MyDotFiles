#!/bin/bash

CACHE_FILE="/tmp/polybar_cpu_cache"

# Leitura atual
STAT=($(grep 'cpu ' /proc/stat))
IDLE=${STAT[4]}
TOTAL=0
for VAL in "${STAT[@]:1}"; do
    TOTAL=$((TOTAL + VAL))
done

# Se tem cache, calcula diferença
if [ -f "$CACHE_FILE" ]; then
    read PREV_TOTAL PREV_IDLE < "$CACHE_FILE"
    DIFF_TOTAL=$((TOTAL - PREV_TOTAL))
    DIFF_IDLE=$((IDLE - PREV_IDLE))
    USAGE=$((100 * (DIFF_TOTAL - DIFF_IDLE) / DIFF_TOTAL))
    echo "$USAGE"
else
    echo "0"
fi

# Salva valores atuais para próxima execução
echo "$TOTAL $IDLE" > "$CACHE_FILE"
