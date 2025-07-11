#!/usr/bin/env bash

# ==================================================
# LAUNCHER POLYBAR OTIMIZADO (MULTI-MONITOR/FAILSAFE)
# Com parada automática de apps Systray
# ==================================================

set -euo pipefail

# 0. EVITAR MÚLTIPLAS EXECUÇÕES
if pgrep -u "$UID" -x polybar >/dev/null; then
    echo "⚠ Polybar já está rodando! Abortando nova execução..."
    exit 1
fi

# 1. LISTA DE APPS DE SYSTRAY: nome simples + comando
declare -A SYSTRAY_APPS_CMDS=(
    [keepassxc]="keepassxc --minimized"
    [nm-applet]="nm-applet"
    [redshift-gtk ]="redshift-gtk "
    [xfce4-clipman]="xfce4-clipman"
    [telegram-desktop]="telegram-desktop -startintray %u"
)

echo ":: Encerrando apps de Systray para evitar conflitos..."
for app in "${!SYSTRAY_APPS_CMDS[@]}"; do
    if pgrep -u "$UID" -x "$app" > /dev/null; then
        echo " - Encerrando $app"
        pkill -u "$UID" -x "$app"
    fi
done

sleep 1

# 2. ENCERRAR INSTÂNCIAS EXISTENTES (COM TIMEOUT MELHORADO)
echo ":: Encerrando instâncias antigas da Polybar..."
killall -q polybar || true

MAX_ATTEMPTS=5  # Reduzido para 5s como padrão mais razoável
KILL_ATTEMPTED=0

for ((i=1; i<=MAX_ATTEMPTS; i++)); do
    if ! pgrep -u "$UID" -x polybar > /dev/null; then
        echo "✔ Polybar encerrado após $i tentativa(s)"
        break
    fi
    
    echo ":: Aguardando encerramento ($i/$MAX_ATTEMPTS)..."
    
    # Na última tentativa, força o encerramento
    if [ $i -eq $MAX_ATTEMPTS ] && [ $KILL_ATTEMPTED -eq 0 ]; then
        echo "⚠ Forçando encerramento com SIGKILL..."
        killall -9 -q polybar || true
        KILL_ATTEMPTED=1
        # Dá mais uma chance após o kill -9
        i=$((i-1))  # Decrementa para repetir o ciclo
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
    MONITORS=("${FALLBACK_MONITOR:-eDP1}")  # Fallback configurável via env
fi

PRIMARY_MONITOR=${MONITORS[0]}

# 4. LANÇAMENTO COM CONTROLE DE ERROS
echo ":: Iniciando Polybar nas seguintes telas: ${MONITORS[*]}"

LOG_FILE="/tmp/polybar.log"
: > "$LOG_FILE"  # Limpa o log antes de começar

for m in "${MONITORS[@]}"; do
    echo ":: Iniciando Polybar no monitor $m"
    {
        MONITOR="$m" polybar -q -r main
        if [ $? -eq 0 ]; then
            echo "✔ Polybar iniciada com sucesso no monitor $m"
        else
            echo "⚠ Falha ao iniciar no monitor $m"
        fi
    } >> "$LOG_FILE" 2>&1 &
    sleep 0.5
done

# 5. LOG FINAL MELHORADO
echo "=========================================="
echo "Polybar launched on ${#MONITORS[@]} monitor(s):"
printf " - %s\n" "${MONITORS[@]}"
echo "Logs disponíveis em: $LOG_FILE"
echo "=========================================="

# 6. OPCIONAL: Reiniciar apps da Systray automaticamente
echo ":: Aguardando Polybar estabilizar..."
sleep 5

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

# Informação sobre fallback
echo ":: Fallback de monitor parametrizável: FALLBACK_MONITOR"
echo "   Exemplo: export FALLBACK_MONITOR=\"eDP1\" no seu .bashrc ou .zshrc"
