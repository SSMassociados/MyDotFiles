#!/bin/bash

# Verifica se jq está instalado
if ! command -v jq &> /dev/null
then
    notify-send "Erro" "jq não está instalado. Instale-o usando o comando apropriado para sua distribuição:
    Debian/Ubuntu: sudo apt install jq
    Fedora: sudo dnf install jq
    Arch Linux: sudo pacman -S jq"
    exit 1
fi

# Diretório de destino
DIR=~/.config/i3/cenarios

# Verifica se o diretório existe, se não existir, cria-o
if [ ! -d "$DIR" ]; then
    mkdir -p "$DIR"
    notify-send "Informação" "Diretório $DIR criado."
else
    notify-send "Informação" "Diretório $DIR já existe."
fi

# Obtém o número do espaço de trabalho ativo
workspace_num=$(i3-msg -t get_workspaces | jq '.[] | select(.focused==true).num')

# Verifica se a obtenção do número do workspace foi bem-sucedida
if [ -z "$workspace_num" ]; then
    notify-send "Erro" "Não foi possível obter o número do espaço de trabalho ativo."
    exit 1
fi

# Salva o layout do espaço de trabalho ativo em um arquivo JSON
i3-save-tree --workspace "$workspace_num" > "$DIR/layout_$workspace_num.json"

# Verifica se o comando i3-save-tree foi bem-sucedido
if [ $? -ne 0 ]; then
    notify-send "Erro" "Não foi possível salvar o layout do espaço de trabalho."
    exit 1
fi

# Processa o arquivo JSON para remover ou ajustar os comentários
#sed -i 's|^\(\s*\)// "|\1"|g; /^\s*\/\//d' "$DIR/layout_$workspace_num.json"
sed -i -e '/"swallows": \[/,/\]/ {s|^\(\s*\)// \("class".*\)$|\1\2|; s|^\(\s*\)// \("instance".*\),|\1\2|; s|\\||g; /^[[:space:]]*\/\//d}' "$DIR/layout_$workspace_num.json"

# Verifica se o comando sed foi bem-sucedido
if [ $? -ne 0 ]; then
    notify-send "Erro" "Não foi possível processar o arquivo JSON."
    exit 1
fi

notify-send "Sucesso" "Layout do espaço de trabalho $workspace_num salvo e processado com sucesso em $DIR/layout_$workspace_num.json"
