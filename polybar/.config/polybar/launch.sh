#!/usr/bin/env bash

# ==================================================
# LAUNCHER POLYBAR OTIMIZADO (MULTI-MONITOR/FAILSAFE)
# ==================================================

# 1. ENCERRAR INSTÂNCIAS EXISTENTES (COM MAIS TOLERÂNCIA)
killall -q polybar || true
while pgrep -u $UID -x polybar >/dev/null; do 
    echo ":: Aguardando encerramento de instâncias existentes..."
    sleep 1
done

# 2. DETECTAR MONITORES ATIVOS COM VALIDAÇÃO
mapfile -t MONITORS < <(xrandr --query | awk '/ connected/ && !/disconnected/ {print $1}')
if [ ${#MONITORS[@]} -eq 0 ]; then
    echo "⚠ Nenhum monitor detectado! Usando fallback..."
    MONITORS=("eDP1")  # Fallback explícito baseado no seu sistema
fi

PRIMARY_MONITOR=${MONITORS[0]}

# 3. LANÇAMENTO COM CONTROLE DE ERROS
for m in "${MONITORS[@]}"; do
    echo ":: Iniciando Polybar no monitor $m"
    if MONITOR=$m polybar -q -r main 2>&1 | tee -a /tmp/polybar.log; then
        echo "✔ Polybar iniciada com sucesso no monitor $m"
    else
        echo "⚠ Falha ao iniciar no monitor $m (ver /tmp/polybar.log)"
    fi &
    sleep 0.5
done

# 4. LOG FINAL MELHORADO
echo "=========================================="
echo "Polybar launched on ${#MONITORS[@]} monitor(s):"
printf " - %s\n" "${MONITORS[@]}"
echo "Logs disponíveis em: /tmp/polybar.log"
echo "=========================================="


##!/bin/bash

## Garante que apenas uma instância do script rode
#if pidof -x "polybar" >/dev/null; then
    #pkill -9 polybar
    ## Espera um pouco para garantir que todas foram encerradas
    #sleep 0.5
#fi

## Define e aplica um novo wallpaper aleatório
#WALLPAPER=$(find ~/.wallpaper -type f \( -name '*.jpg' -o -name '*.png' \) | shuf -n 1)
#if [ -n "$WALLPAPER" ]; then
    #echo "Aplicando wallpaper: $WALLPAPER" | tee -a ~/.cache/polybar.log
    #wal -i "$WALLPAPER" --iterative && \
    #~/.config/dunst/update_dunst_colors.sh
#else
    #echo "Erro: Nenhum wallpaper encontrado em ~/.wallpaper" | tee -a ~/.cache/polybar.log
    #exit 1
#fi

## Carrega as cores do Pywal
#if [ -f ~/.cache/wal/colors.sh ]; then
    #source ~/.cache/wal/colors.sh
#else
    #echo "Erro: Arquivo de cores do Pywal não encontrado." | tee -a ~/.cache/polybar.log
    #exit 1
#fi

## Inicia a polybar com logging
#echo "Iniciando polybar..." | tee -a ~/.cache/polybar.log
#polybar -r main -l info 2>&1 | tee -a ~/.cache/polybar.log & disown
