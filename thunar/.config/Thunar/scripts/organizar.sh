#!/bin/bash
# organizar.sh — Organiza arquivos por tipo de extensão (Linux) - Recursivo com Correção
# Uso: ./organizar.sh [--dry-run] [--help] [pasta]   (padrão: diretório atual)
# Seguro para múltiplas execuções e corrige arquivos em pastas erradas

# ─── Tratamento de erros explícito (sem set -e para não sair em erros benignos) ───
set -uo pipefail

GREEN='\033[1;32m'
CYAN='\033[1;36m'
DIM='\033[0;90m'
BOLD='\033[1m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[1;34m'
RESET='\033[0m'

# ─── Parse de argumentos ───────────────────────────────────────────────────────
DRY_RUN=false
TARGET="."

usage() {
    echo -e "  ${BOLD}Uso:${RESET} $(basename "$0") [--dry-run] [--help] [pasta]"
    echo -e "  ${DIM}  --dry-run   Simula sem mover arquivos${RESET}"
    echo -e "  ${DIM}  --help      Exibe esta ajuda${RESET}"
    echo -e "  ${DIM}  pasta       Diretório alvo (padrão: diretório atual)${RESET}"
    exit 0
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --help|-h) usage ;;
        --*)
            echo -e "${RED}Erro:${RESET} Argumento desconhecido: '$arg'" >&2
            usage ;;
        *)
            TARGET="$arg" ;;
    esac
done

TARGET="${TARGET%/}"

if [ ! -d "$TARGET" ]; then
    echo -e "${BOLD}Erro:${RESET} '$TARGET' não é um diretório válido." >&2
    exit 1
fi

# ─── Hash set de categorias para lookup O(1) ──────────────────────────────────
declare -A CAT_SET=(
    [PDF]=1 [Markdown]=1 [Planilhas]=1 [Documentos]=1
    [Imagens]=1 [Videos]=1 [Audio]=1 [Instaladores]=1
    [Instaladores-Outros]=1 [Compactados]=1 [Codigo]=1
    [Configuracoes]=1 [Logs]=1 [Scripts-Shell]=1
    [Executaveis]=1 [Outros]=1
)

# ─── Mapeamento de extensão → categoria ───────────────────────────────────────
get_category() {
    local ext="$1"
    case "$ext" in
        pdf)
            echo "PDF" ;;
        md|markdown|mdown|mkd|mkdown)
            echo "Markdown" ;;
        xls|xlsx|xlsm|xlsb|csv|ods|numbers)
            echo "Planilhas" ;;
        doc|docx|odt|rtf|tex|pages|epub|mobi|azw|azw3)
            echo "Documentos" ;;
        jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff|heic|heif|raw|cr2|nef|avif|jfif)
            echo "Imagens" ;;
        mp4|mov|avi|mkv|wmv|flv|webm|m4v|mpg|mpeg|ts|m2ts|mts|3gp)
            echo "Videos" ;;
        mp3|wav|flac|aac|ogg|wma|m4a|opus|aiff|alac|ape|wv)
            echo "Audio" ;;
        deb|rpm|appimage|snap|flatpak|run|bin)
            echo "Instaladores" ;;
        exe|msi|dmg|pkg)
            echo "Instaladores-Outros" ;;
        zip|rar|7z|tar|gz|bz2|xz|tgz|zst|Z|LZ|LZMA)
            echo "Compactados" ;;
        # FIX: Scripts-Shell ANTES de Codigo para sh/bash/zsh/fish não caírem em Codigo
        sh|bash|zsh|fish)
            echo "Scripts-Shell" ;;
        py|js|ts|html|css|json|xml|yaml|yml|sql|rb|go|rs|java|c|cpp|h|hpp|swift|kt|lua|r|pl|pm|t|ps1|vbs)
            echo "Codigo" ;;
        conf|config|cfg|ini|properties|env|toml|editorconfig|gitconfig|gitignore|dockerfile)
            echo "Configuracoes" ;;
        log|out|err|debug|trace)
            echo "Logs" ;;
        *)
            echo "Outros" ;;
    esac
}

# ─── Determina categoria completa para um arquivo (extensão + casos especiais) ─
# FIX: lógica unificada em uma única função, chamada uma vez por arquivo
get_category_for_file() {
    local file="$1"
    local filename ext

    filename=$(basename "$file")

    # Extensões compostas (.tar.gz, .tar.bz2, .tar.xz) — detectar primeiro
    if [[ "$filename" =~ \.tar\.(gz|bz2|xz)$ ]]; then
        echo "Compactados"
        return
    fi

    ext="${filename##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')

    # Arquivo sem extensão (nome == extensão extraída)
    if [ "$filename" = "$ext" ] || [ -z "$ext" ]; then
        # Só invoca file(1) quando necessário — evita fork desnecessário
        if file "$file" 2>/dev/null | grep -q "ELF.*executable"; then
            echo "Executaveis"
        else
            echo "Outros"
        fi
        return
    fi

    get_category "$ext"
}

# ─── Verifica se um diretório é uma pasta de categoria — O(1) ─────────────────
# FIX: usa hash set em vez de loop linear O(N×C)
is_category_dir() {
    local basename
    basename=$(basename "$1")
    [[ -n "${CAT_SET[$basename]+x}" ]]
}

# ─── Contadores e acumuladores (fora de subshell — funcionam corretamente) ────
MOVED=0
CORRECTED=0
EMPTY_REMOVED=0
declare -a CORRECTIONS_LIST=()
declare -A category_count=()

echo ""
echo -e "  ${BOLD}Organizador Inteligente de Arquivos${RESET}"
echo -e "  ${DIM}Alvo: ${CYAN}$TARGET${RESET}"

if $DRY_RUN; then
    echo -e "  ${YELLOW}Modo: DRY-RUN — nenhum arquivo será movido${RESET}"
else
    echo -e "  ${DIM}Modo: Recursivo + Correção de pastas erradas${RESET}"
fi
echo ""

# ─── Coleta todos os arquivos em um array — uma única passagem pelo filesystem ─
# FIX: elimina a primeira passagem de contagem; mapfile carrega tudo de uma vez
mapfile -d '' all_files < <(find "$TARGET" -type f ! -name ".*" -print0 2>/dev/null)

# Filtra apenas os que precisam ser movidos
declare -a pending_files=()
for file in "${all_files[@]}"; do
    category=$(get_category_for_file "$file")
    filedir=$(dirname "$file")
    expected_path="$TARGET/$category"
    if [ "$filedir" != "$expected_path" ]; then
        pending_files+=("$file")
    fi
done

TOTAL_FILES=${#pending_files[@]}

echo -e "  ${DIM}Processando arquivos...${RESET}"
echo ""

CURRENT=0

# ─── Loop principal — sem pipe, variáveis propagam corretamente ───────────────
# FIX: while < <(find) em vez de find | while, sem subshell
for file in "${pending_files[@]}"; do
    filename=$(basename "$file")
    filedir=$(dirname "$file")

    category=$(get_category_for_file "$file")
    dest="$TARGET/$category"

    CURRENT=$((CURRENT + 1))
    if [ "$TOTAL_FILES" -gt 0 ]; then
        PROGRESS=$((CURRENT * 100 / TOTAL_FILES))
    else
        PROGRESS=100
    fi

    # Determinar tipo de ação
    ACTION="MOVENDO"
    if is_category_dir "$filedir"; then
        ACTION="CORRIGINDO"
        CORRECTED=$((CORRECTED + 1))
        CORRECTIONS_LIST+=("$filename: $(basename "$filedir") -> $category")
    fi

    # Limpar linha antes de exibir (evita lixo visual de warnings intermediários)
    printf "\r\033[K"

    case "$ACTION" in
        CORRIGINDO)
            printf "  ${YELLOW}[%3d%%] 🔧 CORRIGINDO${RESET} ${CYAN}%s${RESET}/%s ${DIM}(estava em: %s/)${RESET}" \
                "$PROGRESS" "$category" "$filename" "$(basename "$filedir")"
            ;;
        *)
            rel_path="${filedir#"$TARGET"/}"
            [ "$rel_path" = "$filedir" ] && rel_path="."
            printf "  ${BLUE}[%3d%%] →${RESET} ${CYAN}%s${RESET}/%s ${DIM}(de: %s)${RESET}" \
                "$PROGRESS" "$category" "$filename" "$rel_path"
            ;;
    esac

    if $DRY_RUN; then
        # Dry-run: apenas registrar, não mover
        category_count["$category"]=$(( ${category_count["$category"]:-0} + 1 ))
        MOVED=$((MOVED + 1))
        continue
    fi

    # Criar pasta destino
    mkdir -p "$dest"

    # Resolver conflito de nomes
    dest_file="$dest/$filename"
    if [ -e "$dest_file" ]; then
        base="${filename%.*}"
        suffix="${filename##*.}"

        if [ "$filename" = "$suffix" ]; then
            suffix=""
            n=1
            while [ -e "$dest/${base} ($n)" ]; do n=$((n + 1)); done
            dest_file="$dest/${base} ($n)"
        else
            n=1
            while [ -e "$dest/${base} ($n).${suffix}" ]; do n=$((n + 1)); done
            dest_file="$dest/${base} ($n).${suffix}"
        fi

        printf "\r\033[K"
        echo -e "  ${DIM}  ↳ Renomeado para evitar conflito: $(basename "$dest_file")${RESET}"
    fi

    # Mover arquivo
    if mv "$file" "$dest_file" 2>/dev/null; then
        category_count["$category"]=$(( ${category_count["$category"]:-0} + 1 ))
        MOVED=$((MOVED + 1))
    else
        printf "\r\033[K"
        echo -e "  ${RED}  ✗ Falha ao mover: $filename${RESET}"
    fi
done

printf "\r\033[K"
echo ""

# ─── Limpeza de pastas vazias ─────────────────────────────────────────────────
if ! $DRY_RUN; then
    echo -e "  ${DIM}Limpando pastas vazias...${RESET}"

    while IFS= read -r -d '' subdir; do
        [ "$subdir" = "$TARGET" ] && continue
        if [ -z "$(ls -A "$subdir" 2>/dev/null)" ]; then
            if rmdir "$subdir" 2>/dev/null; then
                echo -e "  ${DIM}🗑 Removida pasta vazia:${RESET} ${subdir#"$TARGET"/}"
                EMPTY_REMOVED=$((EMPTY_REMOVED + 1))
            fi
        fi
    done < <(find "$TARGET" -type d -depth -print0 2>/dev/null)
fi

# ─── Resumo final ─────────────────────────────────────────────────────────────
echo ""
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
if $DRY_RUN; then
    echo -e "  ${YELLOW}👁 DRY-RUN CONCLUÍDO — nenhum arquivo foi movido${RESET}"
else
    echo -e "  ${GREEN}✅ ORGANIZAÇÃO CONCLUÍDA${RESET}"
fi
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
echo ""

if [ "$MOVED" -eq 0 ]; then
    echo -e "  ${GREEN}✓${RESET} Nenhum arquivo precisou ser movido."
    echo -e "  ${DIM}Todos os arquivos já estão em suas pastas corretas!${RESET}"
else
    if $DRY_RUN; then
        echo -e "  ${YELLOW}👁${RESET} ${BOLD}Arquivos que seriam movidos: ${MOVED}${RESET}"
    else
        echo -e "  ${GREEN}✓${RESET} ${BOLD}Total de arquivos processados: ${MOVED}${RESET}"
    fi

    if [ "$CORRECTED" -gt 0 ]; then
        echo -e "  ${YELLOW}🔧 Arquivos corrigidos de pastas erradas: ${CORRECTED}${RESET}"
    fi

    echo ""
    echo -e "  ${BOLD}📊 Estatísticas por categoria:${RESET}"
    echo ""

    # Exibir categorias ordenadas por contagem (maior primeiro)
    for cat in "${!category_count[@]}"; do
        echo "${category_count[$cat]} $cat"
    done | sort -rn | while read -r count cat; do
        printf "  ${CYAN}%-22s${RESET} ${BOLD}%3d${RESET} arquivo" "$cat:" "$count"
        [ "$count" -gt 1 ] && echo "s" || echo ""
    done

    echo ""

    if [ "${#CORRECTIONS_LIST[@]}" -gt 0 ]; then
        echo -e "  ${YELLOW}📝 Correções realizadas:${RESET}"
        echo ""
        for line in "${CORRECTIONS_LIST[@]}"; do
            echo -e "  ${DIM}•${RESET} $line"
        done
        echo ""
    fi
fi

echo ""
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
echo -e "  ${BOLD}📁 Localização:${RESET} $TARGET"

if [ "$MOVED" -gt 0 ] && ! $DRY_RUN; then
    CAT_COUNT=$(find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" 2>/dev/null | wc -l)
    echo -e "  ${BOLD}📂 Categorias utilizadas:${RESET} $CAT_COUNT"
fi

if [ "$EMPTY_REMOVED" -gt 0 ]; then
    echo -e "  ${GREEN}🗑 Pastas vazias removidas:${RESET} $EMPTY_REMOVED"
fi

echo ""
if $DRY_RUN; then
    echo -e "  ${BOLD}💡 Dica:${RESET} Execute sem ${CYAN}--dry-run${RESET} para aplicar as mudanças"
else
    echo -e "  ${BOLD}💡 Dica:${RESET} Execute novamente para verificar/corrigir novos arquivos"
    echo -e "  ${DIM}O script é seguro para execuções múltiplas!${RESET}"
fi
echo ""

if ! $DRY_RUN && { [ "$MOVED" -gt 0 ] || [ -n "$(find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" 2>/dev/null)" ]; }; then
    echo -e "  ${DIM}Pastas de categorias atuais:${RESET}"
    find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" 2>/dev/null \
        | sed 's|.*/|    • |' | sort
    echo ""
fi

echo -e "  ${GREEN}✨ Pronto! Sistema organizado e mantido!${RESET}"
echo ""
