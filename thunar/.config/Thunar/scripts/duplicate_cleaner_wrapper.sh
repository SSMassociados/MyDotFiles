#!/usr/bin/env bash
# ================= duplicate_cleaner_wrapper.sh (ADAPTADO i3wm) =================
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${SCRIPT_DIR}/duplicate_cleaner.sh"
TARGET="${1:-$HOME}"

# Verifica se o script de processamento existe
if [ ! -f "$SCRIPT" ]; then
    yad --error --class="DuplicateCleaner" --text="Script duplicate_cleaner.sh não encontrado"; exit 1
fi

# Verifica dependência do yad
command -v yad >/dev/null || { zenity --error --text="Instale o yad"; exit 1; }

# Formulário principal com classe para i3wm
main_form=$(yad --form \
  --class="DuplicateCleaner" \
  --title="Gerenciador de Duplicados" \
  --field="Diretório:DIR" "$TARGET" \
  --field="Tamanho mínimo (bytes):NUM" "1024!0..100000000!1" \
  --field="Modo:CB" "Apenas listar!Listar e deletar!Listar e mover para lixeira" \
  --field="Mostrar no terminal:CHK" "TRUE" \
  --field="Ocultos:CHK" "FALSE" \
  --field="Excluir:" ".git,node_modules,.cache,Trash,.venv,__pycache__" \
  --button="Cancelar:1" --button="Executar:0") || exit 0

IFS='|' read -r TARGET MIN_SIZE MODE USE_TERM SHOW_HIDDEN EXCLUDES <<< "$main_form"

# Construção do comando
CMD=("$SCRIPT" "$TARGET" --min-size "$MIN_SIZE")

[ "$MODE" = "Listar e deletar" ] && CMD+=(--delete)
[ "$MODE" = "Listar e mover para lixeira" ] && CMD+=(--trash)
[ "$SHOW_HIDDEN" = "TRUE" ] && CMD+=(--include-hidden)
[ -n "$EXCLUDES" ] && CMD+=(--exclude "$EXCLUDES")

# Confirmação para ações destrutivas (também com classe)
if [[ "$MODE" != "Apenas listar" ]]; then
    yad --question --class="DuplicateCleaner" --text="Confirma operação de limpeza?" || exit 0
fi

if [ "$USE_TERM" = "TRUE" ]; then
    # Execução via Terminal com classe específica para i3wm
    # Kitty usa --class, xterm usa -class
    kitty --class="DuplicateTerm" -e "${CMD[@]}" || xterm -class "DuplicateTerm" -e "${CMD[@]}"
else
    # Execução via YAD Text Info com classe específica para i3wm
    OUTPUT=$(mktemp)
    "${CMD[@]}" > "$OUTPUT" 2>&1
    yad --text-info \
        --class="DuplicateResult" \
        --title="Resultados da Busca" \
        --filename="$OUTPUT" \
        --width=900 --height=600
    rm -f "$OUTPUT"
fi
