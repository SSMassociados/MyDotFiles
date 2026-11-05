#!/usr/bin/env bash
# ~/.config/polybar/launch.sh

set -eo pipefail

export FZF_DEFAULT_OPTS="${FZF_DEFAULT_OPTS:-}"
export LS_COLORS="${LS_COLORS:-}"

set -u

# 0. EVITAR MÚLTIPLAS EXECUÇÕES SIMULTÂNEAS (Comportamento Mantido)
if pgrep -u "$UID" -x polybar >/dev/null; then
    echo "⚠ Polybar já está rodando! Abortando..."
    exit 1
fi

# 1. APPS DE SYSTRAY
# Ajustado para usar os nomes exatos verificados pelo seu script de debug
declare -A SYSTRAY_APPS_CMDS=(
    [keepassxc]="keepassxc --minimized"
    [nm-applet]="nm-applet"
    [xfce4-clipman]="xfce4-clipman"
    [Telegram]="Telegram -startintray"
    [whatsie]="whatsie"
    [mailspring]="mailspring --password-store=gnome-libsecret --background"
    [redshift-gtk]="redshift-gtk"
)

echo ":: Encerrando apps de Systray antigos..."
for app in "${!SYSTRAY_APPS_CMDS[@]}"; do
    # Usando pkill direto para limpar instâncias órfãs de forma segura
    pkill -u "$UID" -x "$app" || true
done
sleep 1

# 2. ENCERRAR INSTÂNCIAS ANTIGAS DO POLYBAR
echo ":: Encerrando Polybar..."
polybar-msg cmd quit &>/dev/null || killall -q polybar || true

for ((i=1; i<=10; i++)); do
    pgrep -u "$UID" -x polybar > /dev/null || break
    sleep 0.3
done

if pgrep -u "$UID" -x polybar > /dev/null; then
    echo "⚠ Forçando SIGKILL..."
    killall -9 -q polybar || true
    sleep 1
fi

# 3. DETECTAR MONITOR PRIMÁRIO
PRIMARY_MONITOR=$(xrandr --query | awk '/ connected primary/ {print $1; exit}')
PRIMARY_MONITOR="${PRIMARY_MONITOR:-eDP1}"

echo ":: Monitor primário: $PRIMARY_MONITOR"

# 4. LANÇAR BARRAS
LOG_FILE="/tmp/polybar.log"
: > "$LOG_FILE"

# [tray] PRIMEIRO — precisa assumir o systray antes da [main]
echo ":: [tray] → $PRIMARY_MONITOR"
MONITOR="$PRIMARY_MONITOR" polybar -q -r tray >> "$LOG_FILE" 2>&1 &
sleep 2  

# [main] depois — em todos os monitores conectados
while IFS= read -r monitor; do
    echo ":: [main] → $monitor"
    MONITOR="$monitor" polybar -q -r main >> "$LOG_FILE" 2>&1 &
    sleep 0.3
done < <(xrandr --query | awk '/ connected/ && !/disconnected/ {print $1}')

sleep 1

# Garante que a tray fique acima das janelas i3
(sleep 2; for i in {1..5}; do xdo raise -N Polybar 2>/dev/null || true; sleep 1; done) &

# 5. SNIXEMBED
echo ":: Iniciando snixembed..."
pkill -x snixembed || true
sleep 0.5
snixembed &
sleep 3  

# 6. REINICIAR APPS DE SYSTRAY
echo ":: Aguardando Polybar estabilizar..."
sleep 2

echo ":: Reiniciando apps de Systray..."
for app in "${!SYSTRAY_APPS_CMDS[@]}"; do
    # Separando o binário dos argumentos para validação do command -v
    IFS=' ' read -r -a cmd <<< "${SYSTRAY_APPS_CMDS[$app]}"
    
    if command -v "${cmd[0]}" > /dev/null; then
        if pgrep -u "$UID" -x "$app" > /dev/null; then
            echo " - $app já rodando"
        else
            echo " - Iniciando ${cmd[*]}"
            # Executa os comandos expandindo o array corretamente e jogando pro log
            "${cmd[@]}" >> "$LOG_FILE" 2>&1 &
        fi
    else
        echo " - ${cmd[0]} não encontrado"
    fi
done

echo "=========================================="
echo "Monitor primário : $PRIMARY_MONITOR"
echo "Logs             : $LOG_FILE"
echo "=========================================="
