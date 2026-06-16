#!/bin/bash

# ============================================================================
# DOTFILES -- WATCH_CONFIG_I3 -- By: Sidiclei
# Monitoramento automatizado do ecossistema i3wm com atualização de CheatSheet
# ============================================================================

# Configuração base
I3_CONFIG_DIR="$HOME/.config/i3"
CONFIG_FILE="$I3_CONFIG_DIR/config"
MODULES_DIR="$I3_CONFIG_DIR/modules"
SYNC_SCRIPT="$I3_CONFIG_DIR/scripts/sync_cheatsheet.py"
MONITOR_FILES=()

# Verificar se o diretório de configuração existe
if [ ! -d "$I3_CONFIG_DIR" ]; then
    echo "❌ Diretório de configuração não encontrado: $I3_CONFIG_DIR"
    exit 1
fi

# Verificar se o inotifywait está instalado
if ! command -v inotifywait &> /dev/null; then
    echo "❌ O comando 'inotifywait' não está instalado. Instale o pacote inotify-tools."
    exit 1
fi

# Função para verificar se o i3 está rodando
is_i3_running() {
    pgrep -x i3 > /dev/null
}

# Função de reinicialização com feedback e sincronização do CheatSheet
restart_i3() {
    echo "🔄 Alteração detectada nos arquivos de configuração."
    
    # Passo 1: Sincroniza o Cheat Sheet antes de aplicar o restart
    if [ -f "$SYNC_SCRIPT" ]; then
        echo "📝 Atualizando o Cheat Sheet (~/.config/i3/scripts/cheatsheet.md)..."
        if python3 "$SYNC_SCRIPT"; then
            echo "✅ Cheat Sheet atualizado com sucesso."
        else
            echo "⚠️ Falha ao processar o script Python do Cheat Sheet."
        fi
    else
        echo "⚠️ Script de sincronização não encontrado em: $SYNC_SCRIPT"
    fi

    # Passo 2: Reinicia a interface do i3wm
    echo "🔄 Reiniciando i3wm..."
    if output=$(i3-msg restart 2>&1); then
        echo "✅ i3wm reiniciado com sucesso."
    else
        echo "❌ Erro ao reiniciar o i3: $output"
    fi
}

# Função para coletar hashes de todos os arquivos monitorados
get_all_hashes() {
    local hash_list=""
    
    # Hash do arquivo config principal
    if [ -f "$CONFIG_FILE" ]; then
        hash_list+=$(md5sum "$CONFIG_FILE" 2>/dev/null | awk '{print $1}')
        hash_list+="|"
    fi
    
    # Hashes de todos os arquivos .conf na pasta modules
    if [ -d "$MODULES_DIR" ]; then
        for module_file in "$MODULES_DIR"/*.conf; do
            if [ -f "$module_file" ]; then
                hash_list+=$(md5sum "$module_file" 2>/dev/null | awk '{print $1}')
                hash_list+="|"
            fi
        done
    fi
    
    # Hash combinado (ordena para consistência)
    echo "$hash_list" | md5sum | awk '{print $1}'
}

# Função para listar arquivos que serão monitorados
list_monitored_files() {
    echo "📁 Arquivos monitorados:"
    echo "  - $CONFIG_FILE"
    if [ -d "$MODULES_DIR" ]; then
        find "$MODULES_DIR" -name "*.conf" -type f | sed 's/^/  - /'
    else
        echo "  ⚠️ Pasta modules não encontrada: $MODULES_DIR"
    fi
}

# Captura de sinais para saída limpa
trap "echo '🛑 Encerrando monitoramento...'; exit 0" SIGINT SIGTERM

# Verificação inicial do arquivo principal
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Arquivo de configuração principal não encontrado: $CONFIG_FILE"
    exit 1
fi

echo "📡 Monitorando configurações do i3..."
echo "   Diretório base: $I3_CONFIG_DIR"
echo ""
list_monitored_files
echo ""

# Hash inicial combinado
last_combined_hash=$(get_all_hashes)

# Loop principal de monitoramento
while true; do
    # Monitora o diretório inteiro e arquivos específicos por eventos de escrita/modificação
    inotifywait -q -r -e close_write -e move -e create -e delete \
        "$CONFIG_FILE" \
        "$MODULES_DIR" 2>/dev/null
    
    # Pequena pausa de estabilização (debouncing) para garantir que multiplas escritas terminaram
    sleep 1.5
    
    current_combined_hash=$(get_all_hashes)
    
    if [ "$last_combined_hash" != "$current_combined_hash" ]; then
        last_combined_hash=$current_combined_hash
        
        if is_i3_running; then
            restart_i3
        else
            echo "⚠️ i3 não está rodando. Aguardando início..."
            while ! is_i3_running; do
                sleep 2
            done
            echo "✅ i3 detectado. Continuando monitoramento..."
            restart_i3
        fi
    fi
done
