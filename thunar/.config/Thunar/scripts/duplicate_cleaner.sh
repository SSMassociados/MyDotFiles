#!/bin/bash
# duplicate_cleaner.sh - Limpeza de duplicatas (Versão FINAL)
set -eo pipefail

# Cores
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
BOLD='\033[1m'
DIM='\033[0;90m'
RESET='\033[0m'

# Configurações
TARGET=""
MIN_SIZE="1024"
DELETE_MODE=false
TRASH_MODE=false
INCLUDE_HIDDEN=false
EXCLUDE_PATTERNS=""
SHOW_PROGRESS=true
NO_PROMPT=false

# ====================== PARSING ======================
while [[ $# -gt 0 ]]; do
    case $1 in
        --delete)           DELETE_MODE=true; shift ;;
        --trash)            TRASH_MODE=true; shift ;;
        --min-size)         MIN_SIZE="$2"; shift 2 ;;
        --include-hidden)   INCLUDE_HIDDEN=true; shift ;;
        --exclude)          EXCLUDE_PATTERNS="$2"; shift 2 ;;
        --no-progress)      SHOW_PROGRESS=false; shift ;;
        --no-prompt)        NO_PROMPT=true; shift ;;
        -*) echo -e "${RED}Opção desconhecida: $1${RESET}"; exit 1 ;;
        *)
            [ -z "$TARGET" ] && TARGET="$1"
            shift
            ;;
    esac
done

[ -z "$TARGET" ] && TARGET="$(pwd)"
TARGET="${TARGET%/}"

# Validações
if ! [[ "$MIN_SIZE" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}Erro: --min-size deve ser um número (bytes)${RESET}"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo -e "${RED}Erro: 'bc' não encontrado. Instale com: sudo apt install bc${RESET}"
    exit 1
fi

if [ ! -d "$TARGET" ]; then
    echo -e "${RED}Erro: '$TARGET' não é um diretório válido${RESET}"
    exit 1
fi

# ====================== FUNÇÕES ======================
human_size() {
    local bytes=$1
    if [ "$bytes" -ge 1073741824 ]; then
        echo "$(LC_NUMERIC=C echo "scale=1; $bytes / 1073741824" | bc) GB"
    elif [ "$bytes" -ge 1048576 ]; then
        echo "$(LC_NUMERIC=C echo "scale=1; $bytes / 1048576" | bc) MB"
    elif [ "$bytes" -ge 1024 ]; then
        echo "$((bytes / 1024)) KB"
    else
        echo "${bytes} B"
    fi
}

show_notification() {
    local msg="$1"
    if command -v notify-send &> /dev/null; then
        notify-send -t 5000 "Duplicate Cleaner" "$msg"
    fi
    echo -e "$msg"
}

# ====================== CABEÇALHO ======================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║ 🔍 Duplicate File Cleaner for Thunar ║${RESET}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "📂 Diretório: ${BOLD}$TARGET${RESET}"
echo -e "📏 Mínimo: $(human_size "$MIN_SIZE")"

if [ "$DELETE_MODE" = true ]; then
    echo -e "⚠️ Modo: ${RED}DELEÇÃO ATIVADA${RESET}"
elif [ "$TRASH_MODE" = true ]; then
    echo -e "🗑️ Modo: ${RED}MOVER PARA LIXEIRA${RESET}"
else
    echo -e "ℹ️ Modo: ${GREEN}Apenas leitura${RESET}"
fi
echo ""

# ====================== FIND DINÂMICO ======================
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

EXCLUDE_ARGS=()
if [ "$INCLUDE_HIDDEN" = false ]; then
    EXCLUDE_ARGS+=("-not" "-path" "*/.*")
fi

DEFAULT_EXCLUDES=("node_modules" ".venv" "venv" "__pycache__" ".git" "Trash" ".cache" "lost+found")
for pat in "${DEFAULT_EXCLUDES[@]}"; do
    EXCLUDE_ARGS+=("-not" "-path" "*/$pat/*")
done

if [ -n "$EXCLUDE_PATTERNS" ]; then
    IFS=',' read -ra USER_EXCLUDES <<< "$EXCLUDE_PATTERNS"
    for pat in "${USER_EXCLUDES[@]}"; do
        pat=$(echo "$pat" | xargs)
        if [ -n "$pat" ]; then
            EXCLUDE_ARGS+=("-not" "-path" "*/$pat/*" "-not" "-path" "*/$pat")
        fi
    done
fi

echo -ne "📁 Listando arquivos...\r"
find "$TARGET" -type f -size +"${MIN_SIZE}c" "${EXCLUDE_ARGS[@]}" \
    -printf '%s|%p\0' 2>/dev/null > "$TMPDIR_WORK/files.list"

tr '\0' '\n' < "$TMPDIR_WORK/files.list" > "$TMPDIR_WORK/sizes"
total_files=$(wc -l < "$TMPDIR_WORK/sizes" | tr -d ' ')

if [ "$total_files" -eq 0 ]; then
    echo -e "⚠️ Nenhum arquivo encontrado acima do tamanho mínimo"
    show_notification "Nenhum arquivo para analisar"
    exit 0
fi
echo -e "📁 Encontrados: ${BOLD}$total_files${RESET} arquivos"
echo ""

# ====================== AGRUPAMENTO ======================
echo -ne "🔍 Agrupando por tamanho...\r"
cut -d'|' -f1 "$TMPDIR_WORK/sizes" | sort -n | uniq -d > "$TMPDIR_WORK/dup_sizes"

if [ ! -s "$TMPDIR_WORK/dup_sizes" ]; then
    echo -e "✅ ${GREEN}Nenhuma duplicata encontrada!${RESET}"
    show_notification "✅ Nenhuma duplicata encontrada"
    exit 0
fi

> "$TMPDIR_WORK/candidates"
while read -r dup_size; do
    grep "^${dup_size}|" "$TMPDIR_WORK/sizes" >> "$TMPDIR_WORK/candidates" || true
done < "$TMPDIR_WORK/dup_sizes"

candidates=$(wc -l < "$TMPDIR_WORK/candidates" | tr -d ' ')
echo -e "🎯 Candidatos (mesmo tamanho): ${BOLD}$candidates${RESET}"
echo ""

# ====================== HASHES ======================
echo -e "🔐 Calculando hashes SHA-256..."
echo -ne " Progresso: 0%"
> "$TMPDIR_WORK/hashes"
total_candidates=$candidates
processed=0

while IFS='|' read -r size filepath; do
    hash=$(sha256sum "$filepath" 2>/dev/null | awk '{print $1}')
    if [ -n "$hash" ]; then
        echo "$hash|$size|$filepath" >> "$TMPDIR_WORK/hashes"
    fi
    processed=$((processed + 1))
    if [ "$SHOW_PROGRESS" = true ] && [ $((processed % 10)) -eq 0 ]; then
        percent=$((processed * 100 / total_candidates))
        echo -ne "\r Progresso: ${percent}%"
    fi
done < "$TMPDIR_WORK/candidates"
echo -e "\r Progresso: 100% ✅"
echo ""

awk -F'|' '{print $1}' "$TMPDIR_WORK/hashes" | sort | uniq -d > "$TMPDIR_WORK/dup_hashes"

if [ ! -s "$TMPDIR_WORK/dup_hashes" ]; then
    echo -e "✅ ${GREEN}Nenhuma duplicata real encontrada!${RESET}"
    show_notification "✅ Nenhuma duplicata real encontrada"
    exit 0
fi

# ====================== RESULTADOS ======================
echo -e "${YELLOW}════════════════════════════════════════════${RESET}"
echo -e "${BOLD}📊 DUPLICATAS ENCONTRADAS${RESET}"
echo -e "${YELLOW}════════════════════════════════════════════${RESET}"
echo ""

group_num=0
total_dup_files=0
total_recoverable=0

while read -r dup_hash; do
    group_num=$((group_num + 1))
    mapfile -t group_files < <(grep "^${dup_hash}|" "$TMPDIR_WORK/hashes")
    copies=${#group_files[@]}
    first_size=$(echo "${group_files[0]}" | cut -d'|' -f2)
    recoverable=$((first_size * (copies - 1)))
    total_recoverable=$((total_recoverable + recoverable))
    total_dup_files=$((total_dup_files + copies))

    echo -e "${BOLD}📦 Grupo $group_num${RESET} — ${copies} cópias — ${RED}$(human_size "$recoverable") recuperável${RESET}"
    echo -e " ${DIM}Hash: ${dup_hash:0:16}...${RESET}"

    for i in "${!group_files[@]}"; do
        filepath=$(echo "${group_files[$i]}" | cut -d'|' -f3-)
        rel_path="${filepath#$TARGET/}"
        if [ $i -eq 0 ]; then
            echo -e " ${GREEN}● Mantido:${RESET} $rel_path"
        else
            echo -e " ${RED}○ Duplicata:${RESET} $rel_path"
        fi
    done
    echo ""

    printf "%s\n" "${group_files[@]}" > "$TMPDIR_WORK/group_$group_num"
done < "$TMPDIR_WORK/dup_hashes"

echo -e "${YELLOW}────────────────────────────────────────${RESET}"
echo -e "${BOLD}📈 RESUMO FINAL${RESET}"
echo -e " Grupos: ${BOLD}$group_num${RESET}"
echo -e " Arquivos duplicados: ${BOLD}$total_dup_files${RESET}"
echo -e " Espaço recuperável: ${RED}${BOLD}$(human_size "$total_recoverable")${RESET}"
echo -e "${YELLOW}────────────────────────────────────────${RESET}"
echo ""

# ====================== AÇÃO (DELETE / TRASH) ======================
if { [ "$DELETE_MODE" = true ] || [ "$TRASH_MODE" = true ]; } && [ "$group_num" -gt 0 ]; then
    if [ "$TRASH_MODE" = true ]; then
        ACTION_MSG="mover para a lixeira"
        if command -v gio &> /dev/null; then
            TRASH_CMD="gio trash"
        elif command -v trash &> /dev/null; then
            TRASH_CMD="trash"
        else
            TRASH_CMD="rm -f"
        fi
    else
        ACTION_MSG="deletar"
        TRASH_CMD="rm -f"
    fi

    echo -e "${RED}⚠️ MODO DE $ACTION_MSG ATIVADO${RESET}"
    echo -n "Deseja realmente $ACTION_MSG os arquivos duplicados? (s/N): "
    read -r confirm

    if [[ "$confirm" =~ ^[Ss]$ ]]; then
        echo ""
        total_deleted=0
        for ((g=1; g<=group_num; g++)); do
            echo -ne "Processando grupo $g... "
            deleted=0
            first=true
            while IFS='|' read -r hash size filepath; do
                if [ "$first" = true ]; then
                    first=false
                    echo -e "${GREEN}mantendo${RESET} $(basename "$filepath")"
                else
                    if $TRASH_CMD "$filepath" 2>/dev/null; then
                        deleted=$((deleted + 1))
                        echo -e " ${RED}$( [ "$TRASH_MODE" = true ] && echo "movido para lixeira" || echo "deletado" )${RESET} $(basename "$filepath")"
                    fi
                fi
            done < "$TMPDIR_WORK/group_$g"
            total_deleted=$((total_deleted + deleted))
        done
        echo ""
        echo -e "${GREEN}✅ $total_deleted arquivos processados${RESET}"
        echo -e "${GREEN}✅ $(human_size "$total_recoverable") liberados${RESET}"
        show_notification "✅ $total_deleted arquivos processados ($(human_size "$total_recoverable"))"
    else
        echo -e "${YELLOW}Operação cancelada${RESET}"
    fi
fi

# ====================== PROMPT FINAL ======================
echo ""

if [ "$NO_PROMPT" = false ]; then
    if [ -t 0 ] && [ -t 1 ]; then
        read -p "Pressione ENTER para fechar..."
    else
        echo "✅ Concluído! Você pode fechar esta janela."
        sleep 1.5
    fi
else
    echo "✅ Operação finalizada com sucesso."
fi

exit 0
