#!/usr/bin/env bash
# ~/.config/i3/scripts/toggle_mons.sh
#
# Altera o layout de monitores com mons e recria a Polybar.
# Nenhum aplicativo da bandeja é reiniciado.
#
# Uso:
#   toggle_mons.sh           → avança para o próximo layout
#   toggle_mons.sh <N>       → ativa diretamente o layout N (0, 1, 2…)
#   toggle_mons.sh --status  → exibe o layout atual
#   toggle_mons.sh -s        → alias de --status

set -uo pipefail

# ─────────────────────────────────────────────────────────────
# Configurações
# ─────────────────────────────────────────────────────────────
STATE_FILE="$HOME/.mons_state"
MONS="$HOME/.local/bin/mons"
LAUNCH="$HOME/.config/polybar/launch.sh"

DUNST_TIMEOUT=2500
DUNST_TAG="mons_layout"
DUNST_APP="Monitor Layout"

# Descrições e ícones de cada layout (índice = argumento do mons).
DESCRIPTIONS=(
    "Tela Principal"      # 0  mons -o
    "Tela Secundária"     # 1  mons -s
    "Tela Estendida ⬆"   # 2  mons -e top
)

ICONS=(
    "🖥️"
    "📺"
    "🖥️➡️🖥️"
)

NUM_LAYOUTS=${#DESCRIPTIONS[@]}

# ─────────────────────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────────────────────
notify() {
    local icon="$1" msg="$2"
    if command -v dunstify >/dev/null 2>&1; then
        dunstify \
            -u normal \
            -t "$DUNST_TIMEOUT" \
            -a "$DUNST_APP" \
            -h "string:x-dunst-stack-tag:$DUNST_TAG" \
            "$icon  $msg"
    else
        echo "$icon  $msg"
    fi
}

die() {
    notify "⚠️" "$*"
    exit 1
}

# ─────────────────────────────────────────────────────────────
# Dependências
# ─────────────────────────────────────────────────────────────
[[ -x "$MONS"   ]] || die "'mons' não encontrado em: $MONS"
[[ -x "$LAUNCH" ]] || die "'launch.sh' não encontrado em: $LAUNCH"

# ─────────────────────────────────────────────────────────────
# Lê o estado salvo (com validação).
# ─────────────────────────────────────────────────────────────
LAST_INDEX=0
if [[ -f "$STATE_FILE" ]]; then
    read -r LAST_INDEX < "$STATE_FILE" || LAST_INDEX=0
    if ! [[ "$LAST_INDEX" =~ ^[0-9]+$ ]] || \
       (( LAST_INDEX >= NUM_LAYOUTS )); then
        LAST_INDEX=0
    fi
fi

# ─────────────────────────────────────────────────────────────
# Interpreta argumento
# ─────────────────────────────────────────────────────────────
ARG="${1:-}"

if [[ "$ARG" == "--status" || "$ARG" == "-s" ]]; then
    notify "${ICONS[$LAST_INDEX]}" "Atual: ${DESCRIPTIONS[$LAST_INDEX]}"
    exit 0

elif [[ "$ARG" =~ ^[0-9]+$ ]]; then
    (( ARG < NUM_LAYOUTS )) \
        || die "Índice inválido: $ARG  (máximo: $((NUM_LAYOUTS - 1)))"
    NEXT_INDEX="$ARG"

else
    # Sem argumento: avança para o próximo layout em ciclo.
    NEXT_INDEX=$(( (LAST_INDEX + 1) % NUM_LAYOUTS ))
fi

# ─────────────────────────────────────────────────────────────
# Aplica o layout com mons e aguarda o xrandr estabilizar.
# O launch.sh restart também aguarda, mas esperar aqui garante
# que o mons terminou completamente antes de qualquer coisa.
# ─────────────────────────────────────────────────────────────
apply_layout() {
    local idx="$1"
    case "$idx" in
        0) "$MONS" -o ;;
        1) "$MONS" -s ;;
        2) "$MONS" -e top ;;
        *) die "Layout sem mapeamento: $idx" ;;
    esac

    # Aguarda o xrandr reportar ao menos um monitor conectado.
    local i=0
    while ! xrandr --query | grep -q ' connected'; do
        sleep 0.3
        (( i++ < 40 )) || die "xrandr não estabilizou após a troca de layout."
    done

    # Pausa adicional para o kernel/Xorg ajustar resolução e DPI.
    sleep 1
}

# ─────────────────────────────────────────────────────────────
# Execução principal
# ─────────────────────────────────────────────────────────────
if apply_layout "$NEXT_INDEX"; then
    printf '%s\n' "$NEXT_INDEX" > "$STATE_FILE"
    notify "${ICONS[$NEXT_INDEX]}" "${DESCRIPTIONS[$NEXT_INDEX]}"
    "$LAUNCH" restart
else
    die "Falha ao ativar: ${DESCRIPTIONS[$NEXT_INDEX]}"
fi
