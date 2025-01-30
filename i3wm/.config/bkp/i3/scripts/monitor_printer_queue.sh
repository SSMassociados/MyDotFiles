#!/bin/bash

# Função para verificar se há trabalhos de impressão ativos
check_print_jobs() {
    if lpstat -o | grep -q "active"; then
        return 0  # Se houver trabalhos de impressão ativos, retorna 0
    else
        return 1  # Caso contrário, retorna 1
    fi
}

# Variável para controlar o estado de suspensão/hibernação
suspended=false

# Loop infinito para monitorar continuamente a fila de impressão
while true; do
    if check_print_jobs; then
        if [ "$suspended" = true ]; then
            echo "Trabalhos de impressão ativos. Restaurando suspensão/hibernação."
            systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target  # Restaura suspensão e hibernação
            suspended=false
        fi
        echo "Trabalhos de impressão ativos. Impedindo suspensão/hibernação."
        systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target  # Impede suspensão e hibernação
    else
        if [ "$suspended" = false ]; then
            echo "Nenhum trabalho de impressão ativo. Permissão para suspensão/hibernação restaurada."
            systemctl unmask sleep.target suspend.target hibernate.target hybrid-sleep.target  # Restaura suspensão e hibernação
            suspended=true
        fi
    fi
    sleep 60  # Verificar a cada 20 segundos
done
