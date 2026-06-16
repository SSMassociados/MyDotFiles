#!/bin/sh

BAR_HEIGHT=30  # Altura da barra de status
BORDER_SIZE=1  # Tamanho da borda do gerenciador de janelas
YAD_WIDTH=222  # Largura mínima possível do calendário pop-up
YAD_HEIGHT=193 # Altura mínima possível do calendário pop-up
DATE_FORMAT="%a %d %H:%M"  # Formato padrão da data e hora

# Função para exibir o calendário pop-up
show_calendar() {
    local pos_x pos_y
    eval "$(xdotool getmouselocation --shell)"
    eval "$(xdotool getdisplaygeometry --shell)"

    # Calcula a posição X
    if [ "$((X + YAD_WIDTH / 2 + BORDER_SIZE))" -gt "$WIDTH" ]; then
        pos_x=$((WIDTH - YAD_WIDTH - BORDER_SIZE))
    elif [ "$((X - YAD_WIDTH / 2 - BORDER_SIZE))" -lt 0 ]; then
        pos_x=$((BORDER_SIZE))
    else
        pos_x=$((X - YAD_WIDTH / 2))
    fi

    # Calcula a posição Y
    if [ "$Y" -gt "$((HEIGHT / 2))" ]; then
        pos_y=$((HEIGHT - YAD_HEIGHT - BAR_HEIGHT - BORDER_SIZE))
    else
        pos_y=$((BAR_HEIGHT + BORDER_SIZE))
    fi

    # Exibe o calendário pop-up com as opções personalizadas
    yad --calendar --undecorated --fixed --close-on-unfocus --no-buttons \
        --width="$YAD_WIDTH" --height="$YAD_HEIGHT" --posx="$pos_x" --posy="$pos_y" \
        --title="yad-calendar" --borders=0 \
        --color="$CALENDAR_COLOR" --fontname="$CALENDAR_FONT" \
        --format="$DATE_FORMAT" >/dev/null &
}

# Analisa os argumentos
case "$1" in
    --popup)
        # Exibe o calendário pop-up
        if [ "$(xdotool getwindowfocus getwindowname)" = "yad-calendar" ]; then
            exit 0
        fi
        show_calendar
        ;;
    --set-color)
        # Define o esquema de cores do calendário
        CALENDAR_COLOR="$2"
        ;;
    --set-font)
        # Define a fonte do calendário
        CALENDAR_FONT="$2"
        ;;
    --set-date-format)
        # Define o formato de data e hora
        DATE_FORMAT="$2"
        ;;
    *)
        # Exibe a data e hora atual
        echo "$(date +"$DATE_FORMAT")"
        ;;
esac
