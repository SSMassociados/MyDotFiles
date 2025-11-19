#!/bin/bash
# ~/.config/polybar/scripts/quickterm_update_wrapper.sh (Versão Final)

# Este script executa a ação passada ($1) dentro do i3-quickterm,
# instruindo o i3-quickterm a executar seu terminal padrão (kitty)
# e usar o terminal para rodar o script.

# Verifica se um comando foi passado
if [ -z "$1" ]; then
    echo "Erro: Nenhuma ação especificada."
    exit 1
fi

# Ação: Chama o i3-quickterm.
# Nós passamos o comando para rodar o KITTY e instruímos o KITTY (-e) a executar o script ($1).
# Substitua 'kitty' pelo seu terminal se for outro (ex: alacritty, xterm).
i3-quickterm exec kitty -e "$1"

# Opcional: Notificação de erro
if [ $? -ne 0 ]; then
    notify-send -t 3000 "❌ Quickterm/Kitty Falhou" "Verifique o caminho do kitty/i3-quickterm."
fi
