#!/bin/bash

CONFIG_FILE="$HOME/.config/i3/config"

# Verificar se o arquivo de configuração existe
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Arquivo de configuração não encontrado: $CONFIG_FILE"
    exit 1
fi

# Verificar se o inotifywait está instalado
if ! command -v inotifywait &> /dev/null; then
    echo "O comando 'inotifywait' não está instalado. Instale o pacote inotify-tools."
    exit 1
fi

# Função para verificar se o i3 está rodando
is_i3_running() {
    pgrep -x i3 > /dev/null
}

# Função de reinicialização com feedback
restart_i3() {
    echo "Arquivo de configuração alterado. Reiniciando i3..."
    output=$(i3-msg restart 2>&1)
    if [ $? -eq 0 ]; then
        echo "i3 reiniciado com sucesso."
    else
        echo "Erro ao reiniciar o i3: $output"
    fi
}

# Adicionar captura de sinais
trap "echo 'Encerrando monitoramento do arquivo de configuração.'; exit" SIGINT SIGTERM

# Loop para monitorar o arquivo de configuração
last_hash=$(md5sum "$CONFIG_FILE" | awk '{print $1}')
while true; do
    inotifywait -e close_write "$CONFIG_FILE"
    current_hash=$(md5sum "$CONFIG_FILE" | awk '{print $1}')
    if [ "$last_hash" != "$current_hash" ]; then
        last_hash=$current_hash
        if is_i3_running; then
            restart_i3
        else
            echo "i3 não está rodando. Saindo do script."
            break
        fi
    fi
done
