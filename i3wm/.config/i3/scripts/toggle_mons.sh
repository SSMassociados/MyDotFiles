#!/bin/bash

# Arquivo que registra o último comando executado
STATE_FILE="$HOME/.mons_state"

# Comandos para alternar
COMMANDS=("/sbin/mons -e top" "/sbin/mons -o" "/sbin/mons -s")

# Verifica o último comando executado
if [[ -f "$STATE_FILE" ]]; then
    LAST_INDEX=$(cat "$STATE_FILE")
else
    LAST_INDEX=0  # Começa no primeiro comando se o arquivo não existir
fi

# Calcula o próximo índice e executa o comando
NEXT_INDEX=$(( (LAST_INDEX + 1) % ${#COMMANDS[@]} ))
${COMMANDS[$NEXT_INDEX]}

# Salva o índice do comando atual para a próxima execução
echo "$NEXT_INDEX" > "$STATE_FILE"
