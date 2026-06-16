#!/usr/bin/env bash

# ==================================================
# ~/.config/polybar/launch.sh
# LAUNCHER POLYBAR OTIMIZADO (MULTI-MONITOR/FAILSAFE)
# Com parada automática de apps Systray
# Barras: main (por monitor ou só primário) + tray (monitor primário)
# ==================================================

set -eo pipefail

# Garante variáveis externas opcionais antes do set -u.
# Evita abort por "variável não associada" ao ser chamado
# fora do ambiente de login (ex: toggle_mons.sh, i3 reload).
# Cobre todas as variáveis que o pywal/colors.sh pode referenciar.
export FZF_DEFAULT_OPTS="${FZF_DEFAULT_OPTS:-}"
export LSCOLORS="${LSCOLORS:-}"
export LS_COLORS="${LS_COLORS:-}"
export LESS_TERMCAP_mb="${LESS_TERMCAP_mb:-}"
export LESS_TERMCAP_md="${LESS_TERMCAP_md:-}"
export LESS_TERMCAP_me="${LESS_TERMCAP_me:-}"
export LESS_TERMCAP_se="${LESS_TERMCAP_se:-}"
export LESS_TERMCAP_so="${LESS_TERMCAP_so:-}"
export LESS_TERMCAP_ue="${LESS_TERMCAP_ue:-}"
export LESS_TERMCAP_us="${LESS_TERMCAP_us:-}"
export FALLBACK_MONITOR="${FALLBACK_MONITOR:-eDP1}"

set -u

# ==================================================
# OPÇÃO DE MODO DA POLYBAR
#   "primary" → barra [main] apenas no monitor primário
#   "all"     → barra [main] em todos os monitores conectados
# ==================================================
POLYBAR_MODE="all"

# 0. EVITAR MÚLTIPLAS EXECUÇÕES
if pgrep -u "$UID" -x polybar >/dev/null; then
    echo "⚠ Polybar já está rodando! Abortando nova execução..."
    exit 1
fi

# 1. LISTA DE APPS DE SYSTRAY: nome simples + comando
declare -A SYSTRAY_APPS_CMDS=(
    [keepassxc]="keepassxc --minimized"
    [nm-applet]="nm-applet"
    [xfce4-clipman]="xfce4-clipman"
    [Telegram]="Telegram -startintray"
    [whatsie]="whatsie"
    [mailspring]="mailspring --password-store=gnome-libsecret --background"
    [redshift-gtk]="redshift-gtk"
)

echo ":: Encerrando apps de Systray para evitar conflitos..."
for app in "${!SYSTRAY_APPS_CMDS[@]}"; do
    if pgrep -u "$UID" -x "$app" > /dev/null; then
        echo " - Encerrando $app"
        pkill -u "$UID" -x "$app" || true
    fi
done

sleep 1

# 2. ENCERRAR INSTÂNCIAS EXISTENTES (COM TIMEOUT MELHORADO)
echo ":: Encerrando instâncias antigas da Polybar..."
killall -q polybar || true

MAX_ATTEMPTS=5
KILL_ATTEMPTED=0

for ((i=1; i<=MAX_ATTEMPTS; i++)); do
    if ! pgrep -u "$UID" -x polybar > /dev/null; then
        echo "✔ Polybar encerrado após $i tentativa(s)"
        break
    fi

    echo ":: Aguardando encerramento ($i/$MAX_ATTEMPTS)..."

    if [ $i -eq $MAX_ATTEMPTS ] && [ $KILL_ATTEMPTED -eq 0 ]; then
        echo "⚠ Forçando encerramento com SIGKILL..."
        killall -9 -q polybar || true
        KILL_ATTEMPTED=1
        i=$((i-1))
    else
        sleep 1
    fi
done

if pgrep -u "$UID" -x polybar > /dev/null; then
    echo "⚠⚠ Não foi possível encerrar o Polybar após $MAX_ATTEMPTS tentativas!"
    echo ":: Você pode tentar manualmente com: killall -9 polybar"
    exit 1
fi

# 3. DETECTAR MONITORES ATIVOS COM VALIDAÇÃO
mapfile -t MONITORS < <(xrandr --query | awk '/ connected/ && !/disconnected/ {print $1}')

if [ ${#MONITORS[@]} -eq 0 ]; then
    echo "⚠ Nenhum monitor detectado! Usando fallback..."
    MONITORS=("$FALLBACK_MONITOR")
fi

# Detecta o monitor marcado como primary pelo xrandr.
# Fallback para o primeiro da lista se nenhum estiver marcado,
# e para FALLBACK_MONITOR se a lista estiver vazia.
PRIMARY_MONITOR=$(xrandr --query | awk '/ connected primary/ {print $1; exit}')
if [[ -z "$PRIMARY_MONITOR" ]]; then
    PRIMARY_MONITOR="${MONITORS[0]:-$FALLBACK_MONITOR}"
fi

# 4. LANÇAMENTO COM CONTROLE DE ERROS
LOG_FILE="/tmp/polybar.log"
: > "$LOG_FILE"

# 4a. BARRA MAIN — primário ou todos, conforme POLYBAR_MODE
if [[ "$POLYBAR_MODE" == "all" ]]; then
    echo ":: Iniciando Polybar em todos os monitores: ${MONITORS[*]}"
    for m in "${MONITORS[@]}"; do
        echo ":: Iniciando barra [main] no monitor $m"
        (
            MONITOR="$m" polybar -q -r main >> "$LOG_FILE" 2>&1
            echo "✔ [main] iniciada no monitor $m" >> "$LOG_FILE"
        ) &
        sleep 0.5
    done
else
    echo ":: Iniciando Polybar apenas no monitor primário: $PRIMARY_MONITOR"
    (
        MONITOR="$PRIMARY_MONITOR" polybar -q -r main >> "$LOG_FILE" 2>&1
        echo "✔ [main] iniciada no monitor $PRIMARY_MONITOR" >> "$LOG_FILE"
    ) &
fi

# Aguarda a(s) instância(s) main subirem antes de lançar a tray
sleep 1

# 4b. BARRA TRAY — sempre no monitor primário
echo ":: Iniciando barra [tray] no monitor primário ($PRIMARY_MONITOR)"
(
    MONITOR="$PRIMARY_MONITOR" polybar -q -r tray >> "$LOG_FILE" 2>&1
    echo "✔ [tray] iniciada no monitor $PRIMARY_MONITOR" >> "$LOG_FILE"
) &

# Aguarda a tray renderizar e força acima das janelas do i3
(
    sleep 2
    for i in 1 2 3 4 5; do
        xdo raise -N Polybar 2>/dev/null || true
        sleep 1
    done
) &

# 5. LOG FINAL
echo "=========================================="
echo "Modo polybar : $POLYBAR_MODE"
echo "Monitor primário : $PRIMARY_MONITOR"
echo "Monitores conectados: ${MONITORS[*]}"
echo "Logs disponíveis em : $LOG_FILE"
echo "=========================================="

echo ":: Iniciando tradutor de ícones SNI..."
pkill -x snixembed || true
timeout 3 bash -c 'while pgrep -x snixembed > /dev/null; do sleep 0.2; done' || true
snixembed --fork &
sleep 2

# 6. REINICIAR APPS DA SYSTRAY
echo ":: Aguardando Polybar estabilizar..."
sleep 7

echo ":: Reiniciando apps de Systray..."
for app in "${!SYSTRAY_APPS_CMDS[@]}"; do
    IFS=' ' read -r -a cmd <<< "${SYSTRAY_APPS_CMDS[$app]}"
    if command -v "${cmd[0]}" > /dev/null; then
        if ! pgrep -u "$UID" -x "$app" > /dev/null; then
            echo " - Iniciando ${cmd[*]} &"
            "${cmd[@]}" &
        else
            echo " - $app já está rodando."
        fi
    else
        echo " - ${cmd[0]} não encontrado no sistema."
    fi
done

echo ":: Fallback de monitor parametrizável: FALLBACK_MONITOR"
echo "   Exemplo: export FALLBACK_MONITOR=\"eDP1\" no seu ~/.config/i3/env.sh"
