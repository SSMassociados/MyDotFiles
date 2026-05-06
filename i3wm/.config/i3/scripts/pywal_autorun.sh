#!/usr/bin/env bash

# Pasta de wallpapers
DIR="$HOME/.wallpaper"

# Seleciona um wallpaper aleatório
WALLPAPER=$(find -L "$DIR" -type f \( -iname '*.jpg' -o -iname '*.png' \) | shuf -n 1)

# Verifica se existe
if [[ -z "$WALLPAPER" ]]; then
    notify-send "❌ Nenhum wallpaper encontrado em $DIR"
    exit 1
fi

# Detecta comando do pywal
PYWAL_BIN=$(command -v wal || true)
if [[ -z "$PYWAL_BIN" ]]; then
    notify-send "❌ pywal não encontrado!"
    exit 1
fi

# Detecta comando do feh
FEH_BIN=$(command -v feh || true)
if [[ -z "$FEH_BIN" ]]; then
    notify-send "❌ feh não encontrado!"
    exit 1
fi

# Pywal16?
if "$PYWAL_BIN" --help 2>&1 | grep -q -- '--cols16'; then
    IS_PYWAL16=true
else
    IS_PYWAL16=false
fi

# Evita múltiplos feh abertos
pkill feh 2>/dev/null || true

# Aplica tema com base na versão
if [[ "$IS_PYWAL16" == "true" ]]; then
    # pywal16: usa feh manualmente e modo 16 cores
    "$PYWAL_BIN" -i "$WALLPAPER" --cols16 --backend feh
    feh --bg-fill "$WALLPAPER"
else
    # pywal original: já define o wallpaper e suporta 256+ cores, nesse modo o pywal já chama o feh internamente
    "$PYWAL_BIN" -i "$WALLPAPER" --iterative
fi

# Seta variáveis de cor se existirem. Carrega paleta
[ -f "$HOME/.cache/wal/colors.sh" ] && source "$HOME/.cache/wal/colors.sh"

# --- ATUALIZA SERVIÇOS ---

# 1. Dunst
if [ -f "$HOME/.config/dunst/update_dunst_colors.sh" ]; then
    "$HOME/.config/dunst/update_dunst_colors.sh" &
fi

## 2. Walker (Adicionado)
## 1. Garante que o Elephant (Backend) está rodando
## (Só inicia se não estiver rodando)
#if ! pgrep -x "elephant" > /dev/null; then
    #notify-send "🐘 Elephant" "Iniciando backend..."
    #elephant > /dev/null 2>&1 &
#fi

## 2. Reinicia o Walker (Frontend) para aplicar as novas Cores
#pkill walker
#sleep 0.1
#walker --gapplication-service > /dev/null 2>&1 &

# 3. AltTab
#if [ -f "$HOME/.config/i3/scripts/alttab_pywal.py" ]; then
    #"$HOME/.config/i3/scripts/alttab_pywal.py" &
#fi

# 4. Polybar (Adicionei um pkill para garantir que não acumule processos)
pkill polybar
sleep 0.2
if [ -f "$HOME/.config/polybar/launch.sh" ]; then
    "$HOME/.config/polybar/launch.sh" &
fi

#notify-send "🎨 Pywal" "Cores sincronizadas com o sistema!"
