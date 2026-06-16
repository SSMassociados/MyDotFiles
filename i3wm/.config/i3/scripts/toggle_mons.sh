#!/bin/bash
# toggle_mons.sh — Gerenciador de layouts de monitor para i3wm
# Uso:
#   toggle_mons.sh           → avança para o próximo layout (ciclo)
#   toggle_mons.sh <N>       → vai direto para o layout N (0, 1, 2...)
#   toggle_mons.sh --status  → exibe o layout atual via dunstify
#   toggle_mons.sh -s        → alias de --status

# ── Configurações ────────────────────────────────────────────────────────────
STATE_FILE="$HOME/.mons_state"
MONS_PATH="/usr/bin/mons"
POLYBAR_LAUNCHER="$HOME/.config/polybar/launch.sh"
DUNST_TIMEOUT=2000
DUNST_APP_NAME="Monitor Layout"

DESCRIPTIONS=("Tela Principal" "Tela Secundária" "Tela Estendida ⬆")
ICONS=("🖥️" "📺" "🖥️➡️🖥️")
NUM_LAYOUTS=3

# Executa mons com os argumentos corretos para cada layout.
# O sleep ao final aguarda o Xorg aplicar completamente a reconfiguração
# antes de qualquer outra ação — sem ele a polybar sobe antes do eDP1
# estar disponível como saída e falha com "Monitor not found".
run_mons() {
    case "$1" in
        0) "$MONS_PATH" -o      ;;  # apenas monitor principal
        1) "$MONS_PATH" -s      ;;  # apenas monitor secundário
        2) "$MONS_PATH" -e top  ;;  # estendido: secundário acima
    esac
    sleep 1.5
}

# Encerra a polybar graciosamente e relança via launcher.
relaunch_polybar() {
    polybar-msg cmd quit &>/dev/null || true

    local attempts=0
    while pgrep -u "$UID" -x polybar &>/dev/null && (( attempts < 10 )); do
        sleep 0.3
        (( attempts++ ))
    done

    "$POLYBAR_LAUNCHER" &
}

# ── Verifica dependências ────────────────────────────────────────────────────
if ! command -v "$MONS_PATH" &>/dev/null; then
    dunstify -u critical -a "$DUNST_APP_NAME" \
        "⚠️ Erro" "'mons' não encontrado em $MONS_PATH"
    exit 1
fi

# ── Função de notificação ────────────────────────────────────────────────────
notify() {
    local icon="$1"
    local message="$2"

    if command -v dunstify &>/dev/null; then
        dunstify \
            -u normal \
            -t "$DUNST_TIMEOUT" \
            -a "$DUNST_APP_NAME" \
            -h "string:x-dunst-stack-tag:mons_layout" \
            "$icon $message"
    else
        echo "$icon $message"
    fi
}

# ── Lê estado anterior ───────────────────────────────────────────────────────
if [[ -f "$STATE_FILE" ]]; then
    LAST_INDEX=$(< "$STATE_FILE")
    if ! [[ "$LAST_INDEX" =~ ^[0-9]+$ ]] || \
       (( LAST_INDEX < 0 || LAST_INDEX >= NUM_LAYOUTS )); then
        LAST_INDEX=0
    fi
else
    LAST_INDEX=0
fi

# ── Interpreta argumentos ────────────────────────────────────────────────────
if [[ "$1" == "--status" || "$1" == "-s" ]]; then
    notify "${ICONS[$LAST_INDEX]}" "Atual: ${DESCRIPTIONS[$LAST_INDEX]}"
    exit 0
elif [[ "$1" =~ ^[0-9]+$ ]]; then
    if (( $1 < NUM_LAYOUTS )); then
        NEXT_INDEX="$1"
    else
        notify "⚠️" "Índice inválido: $1 (máximo: $(( NUM_LAYOUTS - 1 )))"
        exit 1
    fi
else
    NEXT_INDEX=$(( (LAST_INDEX + 1) % NUM_LAYOUTS ))
fi

# ── Executa mons, atualiza estado e relança polybar ──────────────────────────
if run_mons "$NEXT_INDEX"; then
    echo "$NEXT_INDEX" > "$STATE_FILE"
    notify "${ICONS[$NEXT_INDEX]}" "${DESCRIPTIONS[$NEXT_INDEX]}"
    relaunch_polybar
else
    notify "⚠️" "Falha ao ativar: ${DESCRIPTIONS[$NEXT_INDEX]}"
    exit 1
fi
