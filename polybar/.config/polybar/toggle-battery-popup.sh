#!/bin/bash

# Verifica se o terminal está disponível
TERMINAL=""
for term in kitty alacritty xterm; do
    if command -v $term >/dev/null; then
        TERMINAL=$term
        break
    fi
done

[ -z "$TERMINAL" ] && notify-send "Erro" "Nenhum terminal encontrado" && exit 1

# Função para abrir no terminal selecionado
case $TERMINAL in
    kitty)
        kitty --class BatteryPopup \
              --config NONE \
              -o initial_window_width=40c \
              -o initial_window_height=10c \
              -o hide_window_decorations=yes \
              -e bash -c "~/.config/polybar/battery-script.sh; read -p 'Pressione Enter para sair...'"
        ;;
    alacritty)
        alacritty --class BatteryPopup \
                  -o "window.dimensions.columns=40" \
                  -o "window.dimensions.lines=10" \
                  -o "window.decorations=none" \
                  -e bash -c "~/.config/polybar/battery-script.sh; read -p 'Pressione Enter para sair...'"
        ;;
    xterm)
        xterm -class BatteryPopup -geometry 40x10 -e "bash -c '~/.config/polybar/battery-script.sh; read -p \"Pressione Enter para sair...\"'"
        ;;
esac
