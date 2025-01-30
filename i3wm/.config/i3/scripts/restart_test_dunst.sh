# Caminho para o arquivo de configuração do Dunst
DUNST_CONFIG="$HOME/.config/dunst/dunstrc"

# Função para reiniciar o Dunst
restart_dunst() {
    echo "Reiniciando o Dunst..."
    killall dunst 2>/dev/null
    dunst --config "$DUNST_CONFIG" &
    sleep 0.5  # Espera para garantir que o Dunst foi iniciado
}

# Função para enviar notificações de teste
send_test_notifications() {
    echo "Enviando notificações de teste..."
    notify-send -u low "Teste Baixa Urgência" "Notificação de baixa urgência"
    notify-send -u normal "Teste Normal" "Notificação de urgência normal"
    notify-send -u critical "Teste Crítico" "Notificação de urgência crítica"
}

# Executa as ações
restart_dunst
send_test_notifications

echo "Dunst reiniciado e notificações enviadas."
