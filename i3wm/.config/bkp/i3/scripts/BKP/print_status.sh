#!/bin/bash

# Função para exibir notificação visual
exibir_notificacao() {
    dunstify -u normal -a 'Status de Impressão' "$1"
}

# Função para verificar o status do trabalho de impressão
verificar_status_impressao() {
    # Obter o número total de páginas do último trabalho de impressão
    total_paginas=$(lpstat -o | tail -n 1 | awk '{print $5}')

    # Obter o número de páginas já impressas do último trabalho de impressão
    paginas_impressas=$(lpstat -o | tail -n 1 | awk '{print $3}')

    # Calcular o número de páginas restantes
    paginas_restantes=$((total_paginas - paginas_impressas))

    # Exibir o resultado
    mensagem="Faltam $paginas_restantes páginas para terminar o trabalho de impressão."
    echo "$mensagem"

    # Exibir notificação visual
    exibir_notificacao "$mensagem"
}

# Loop infinito para verificar o status periodicamente
while true; do
    # Verificar o status do trabalho de impressão
    verificar_status_impressao

    # Verificar se o trabalho de impressão foi concluído
    if [ $paginas_restantes -eq 0 ]; then
        # Emitir notificação sonora
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga
        break
    fi

    # Esperar 10 segundos antes de verificar novamente
    sleep 10
done
