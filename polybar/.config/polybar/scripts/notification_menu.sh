#!/bin/bash

# Captura o histórico de notificações em JSON
history=$(dunstctl history)

# Diagnóstico: Salvar o histórico bruto para análise
echo "$history" > /tmp/dunst_history_debug.json

# Extrai notificações com base na estrutura do JSON
notifications=$(echo "$history" | jq -r '.data[] | .[0] | "\(.id.data): \(.summary.data) - \(.body.data)"')

# Verifica se o histórico está vazio
if [[ -z "$notifications" ]]; then
    notify-send "Histórico vazio" "Nenhuma notificação disponível no momento."
    exit 0
fi

# Exibe o menu com as notificações
chosen=$(echo "$notifications" | rofi -dmenu -i -p "Notificações")

if [[ -z "$chosen" ]]; then
    exit 0
fi

# Extrai o ID da notificação escolhida
chosen_id=$(echo "$chosen" | cut -d':' -f1)

# Verifica se o ID foi extraído corretamente
if [[ -z "$chosen_id" ]]; then
    notify-send "Erro" "Não foi possível identificar a notificação selecionada."
    exit 1
fi

# Tenta executar ação associada à notificação
action=$(dunstctl context "$chosen_id" | jq -r '.actions[0] | .key')

if [[ "$action" != "null" ]] && [[ -n "$action" ]]; then
    dunstctl action "$chosen_id" "$action"
else
    notify-send "Sem ação" "Nenhuma ação associada a esta notificação."
fi
