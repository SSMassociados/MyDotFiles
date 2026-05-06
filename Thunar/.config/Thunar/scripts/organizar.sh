#!/bin/bash
# organizar.sh — Organiza arquivos por tipo de extensao (Linux) - Recursivo com Correção
# Uso: ./organizar.sh [pasta]   (padrao: diretorio atual)
# Seguro para múltiplas execuções e corrige arquivos em pastas erradas

set -eo pipefail

GREEN='\033[1;32m'
CYAN='\033[1;36m'
DIM='\033[0;90m'
BOLD='\033[1m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[1;34m'
RESET='\033[0m'

TARGET="${1:-.}"
TARGET="${TARGET%/}"

if [ ! -d "$TARGET" ]; then
    echo -e "${BOLD}Erro:${RESET} '$TARGET' nao e um diretorio valido." >&2
    exit 1
fi

# Lista de categorias válidas
CATEGORIES=(
    "PDF"
    "Markdown"
    "Planilhas"
    "Documentos"
    "Imagens"
    "Videos"
    "Audio"
    "Instaladores"
    "Instaladores-Outros"
    "Compactados"
    "Codigo"
    "Configuracoes"
    "Logs"
    "Scripts-Shell"
    "Executaveis"
    "Outros"
)

get_category() {
    local ext="$1"
    case "$ext" in
        # PDF (categoria especifica)
        pdf)
            echo "PDF" ;;
        
        # Markdown (categoria especifica)
        md|markdown|mdown|mkd|mkdown)
            echo "Markdown" ;;
        
        # Planilhas (categoria especifica)
        xls|xlsx|xlsm|xlsb|csv|ods|numbers)
            echo "Planilhas" ;;
        
        # Documentos (sem PDF e planilhas)
        doc|docx|odt|rtf|tex|pages|epub|mobi|azw|azw3)
            echo "Documentos" ;;
        
        # Imagens
        jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff|heic|heif|raw|cr2|nef|avif|jfif)
            echo "Imagens" ;;
        
        # Videos
        mp4|mov|avi|mkv|wmv|flv|webm|m4v|mpg|mpeg|ts|m2ts|mts|3gp)
            echo "Videos" ;;
        
        # Audio
        mp3|wav|flac|aac|ogg|wma|m4a|opus|aiff|alac|ape|wv)
            echo "Audio" ;;
        
        # Instaladores Linux
        deb|rpm|appimage|snap|flatpak|run|bin)
            echo "Instaladores" ;;
        
        # Instaladores Windows (separado por compatibilidade)
        exe|msi|dmg|pkg)
            echo "Instaladores-Outros" ;;
        
        # Compactados
        zip|rar|7z|tar|gz|bz2|xz|tgz|zst|tar\.gz|tar\.bz2|tar\.xz|Z|LZ|LZMA)
            echo "Compactados" ;;
        
        # Codigo/Programacao
        py|js|html|css|sh|bash|zsh|fish|json|xml|yaml|yml|sql|rb|go|rs|java|c|cpp|h|hpp|swift|kt|lua|r|pl|pm|t|ps1|vbs)
            echo "Codigo" ;;
        
        # Configuracoes
        conf|config|cfg|ini|properties|env|toml|editorconfig|gitconfig|gitignore|dockerfile)
            echo "Configuracoes" ;;
        
        # Logs
        log|out|err|debug|trace)
            echo "Logs" ;;
        
        # Scripts Shell
        sh|bash|zsh|fish)
            echo "Scripts-Shell" ;;
        
        *)
            echo "Outros" ;;
    esac
}

# Verificar se um diretório é uma pasta de categoria
is_category_dir() {
    local dir="$1"
    local basename=$(basename "$dir")
    for cat in "${CATEGORIES[@]}"; do
        if [ "$basename" = "$cat" ]; then
            return 0
        fi
    done
    return 1
}

# Contadores
MOVED=0
CORRECTED=0
declare -A category_count
TEMP_LOG=$(mktemp)
CORRECTIONS_LOG=$(mktemp)
trap 'rm -f "$TEMP_LOG" "$CORRECTIONS_LOG"' EXIT

echo ""
echo -e "  ${BOLD}Organizador Inteligente de Arquivos${RESET}"
echo -e "  ${DIM}Alvo: ${CYAN}$TARGET${RESET}"
echo -e "  ${DIM}Modo: Recursivo + Correção de pastas erradas${RESET}"
echo ""

# Primeira passagem: Contar arquivos totais (excluindo os já corretamente organizados)
TOTAL_FILES=0
while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    ext=$(echo "${filename##*.}" | tr '[:upper:]' '[:lower:]')
    
    # Determinar categoria correta
    if [ "$filename" = "$ext" ] || [ -z "$ext" ]; then
        if file "$file" | grep -q "ELF.*executable"; then
            expected_category="Executaveis"
        else
            expected_category="Outros"
        fi
    else
        expected_category=$(get_category "$ext")
    fi
    
    filedir=$(dirname "$file")
    expected_path="$TARGET/$expected_category"
    
    # Só conta se não estiver já na categoria correta
    if [ "$filedir" != "$expected_path" ]; then
        TOTAL_FILES=$((TOTAL_FILES + 1))
    fi
done < <(find "$TARGET" -type f ! -name ".*" -print0 2>/dev/null)

CURRENT=0

echo -e "  ${DIM}Processando arquivos...${RESET}"
echo ""

# Processar arquivos recursivamente
find "$TARGET" -type f ! -name ".*" -print0 2>/dev/null | while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    filedir=$(dirname "$file")
    
    # Extrair extensao (lowercase)
    ext=$(echo "${filename##*.}" | tr '[:upper:]' '[:lower:]')
    
    # Tratar arquivos com multiplas extensoes (ex: .tar.gz)
    if [[ "$filename" =~ \.tar\.(gz|bz2|xz)$ ]]; then
        ext="tar.${BASH_REMATCH[1]}"
    fi
    
    # Determinar categoria correta baseada na extensão
    if [ "$filename" = "$ext" ] || [ -z "$ext" ]; then
        # Verificar se é executável (ELF)
        if file "$file" | grep -q "ELF.*executable"; then
            category="Executaveis"
        else
            category="Outros"
        fi
    else
        category=$(get_category "$ext")
    fi
    
    dest="$TARGET/$category"
    expected_path="$dest"
    
    # Verificar se o arquivo já está na pasta correta
    if [ "$filedir" = "$expected_path" ]; then
        # Já está corretamente organizado, pular
        continue
    fi
    
    # Atualizar progresso
    CURRENT=$((CURRENT + 1))
    if [ $TOTAL_FILES -gt 0 ]; then
        PROGRESS=$((CURRENT * 100 / TOTAL_FILES))
    else
        PROGRESS=100
    fi
    
    # Determinar tipo de ação
    ACTION=""
    if [[ "$filedir" == "$TARGET/"* ]]; then
        parent_dir=$(basename "$filedir")
        if is_category_dir "$filedir"; then
            ACTION="CORRIGINDO"
            CORRECTED=$((CORRECTED + 1))
            echo "$filename: $parent_dir -> $category" >> "$CORRECTIONS_LOG"
        else
            ACTION="MOVENDO"
        fi
    else
        ACTION="MOVENDO"
    fi
    
    # Mostrar ação
    rel_path="${filedir#$TARGET/}"
    [ "$rel_path" = "$filedir" ] && rel_path="."
    
    case "$ACTION" in
        "CORRIGINDO")
            printf "\r  ${YELLOW}[%3d%%] 🔧 CORRIGINDO${RESET} ${CYAN}$category${RESET}/$filename ${DIM}(estava em: $(basename "$filedir")/)${RESET}" "$PROGRESS"
            ;;
        *)
            printf "\r  ${BLUE}[%3d%%] →${RESET} ${CYAN}$category${RESET}/$filename ${DIM}(de: $rel_path)${RESET}" "$PROGRESS"
            ;;
    esac
    
    # Criar pasta destino
    mkdir -p "$dest"
    
    # Resolver conflito de nomes
    dest_file="$dest/$filename"
    if [ -e "$dest_file" ]; then
        base="${filename%.*}"
        suffix="${filename##*.}"
        
        # Se arquivo sem extensão
        if [ "$filename" = "$suffix" ]; then
            suffix=""
            n=1
            while [ -e "$dest/$base ($n)" ]; do
                n=$((n + 1))
            done
            dest_file="$dest/$base ($n)"
        else
            n=1
            while [ -e "$dest/$base ($n).$suffix" ]; do
                n=$((n + 1))
            done
            dest_file="$dest/$base ($n).$suffix"
        fi
        
        # Avisar sobre renomeação
        if [ "$ACTION" = "CORRIGINDO" ]; then
            echo -e "\n  ${DIM}  ↳ Renomeado para evitar conflito: $(basename "$dest_file")${RESET}"
        fi
    fi
    
    # Mover arquivo
    mv "$file" "$dest_file"
    echo "$category" >> "$TEMP_LOG"
    MOVED=$((MOVED + 1))
done

# Garantir que os contadores sejam capturados corretamente
if [ -f "$TEMP_LOG" ]; then
    MOVED=$(wc -l < "$TEMP_LOG")
fi

if [ -f "$CORRECTIONS_LOG" ]; then
    CORRECTED=$(wc -l < "$CORRECTIONS_LOG")
fi

echo ""
echo ""

# Remover pastas vazias (exceto pastas de categoria)
echo -e "  ${DIM}Limpando pastas vazias...${RESET}"
EMPTY_REMOVED=0

find "$TARGET" -type d -depth -print0 2>/dev/null | while IFS= read -r -d '' subdir; do
    # Não remover o diretório alvo principal
    if [ "$subdir" = "$TARGET" ]; then
        continue
    fi
    
    # Não remover pastas de categoria (mesmo que vazias)
    #if is_category_dir "$subdir"; then
        #continue
    #fi
    
    # Verificar se o diretório está vazio
    if [ -z "$(ls -A "$subdir" 2>/dev/null)" ]; then
        rmdir "$subdir" 2>/dev/null && {
            echo -e "  ${DIM}🗑 Removida pasta vazia:${RESET} ${subdir#$TARGET/}"
            EMPTY_REMOVED=$((EMPTY_REMOVED + 1))
        }
    fi
done

# Resumo final
echo ""
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
echo -e "  ${GREEN}✅ ORGANIZAÇÃO CONCLUÍDA${RESET}"
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
echo ""

if [ $MOVED -eq 0 ]; then
    echo -e "  ${GREEN}✓${RESET} Nenhum arquivo precisou ser movido."
    echo -e "  ${DIM}Todos os arquivos já estão em suas pastas corretas!${RESET}"
else
    echo -e "  ${GREEN}✓${RESET} ${BOLD}Total de arquivos processados: ${MOVED}${RESET}"
    
    if [ $CORRECTED -gt 0 ]; then
        echo -e "  ${YELLOW}🔧 Arquivos corrigidos de pastas erradas: ${CORRECTED}${RESET}"
    fi
    
    echo ""
    echo -e "  ${BOLD}📊 Estatísticas por categoria:${RESET}"
    echo ""
    
    # Mostrar estatisticas por categoria
    sort "$TEMP_LOG" | uniq -c | sort -rn | while read -r count cat; do
        printf "  ${CYAN}%-20s${RESET} ${BOLD}%3d${RESET} arquivo" "$cat:" "$count"
        [ $count -gt 1 ] && echo "s" || echo ""
    done
    
    echo ""
    
    # Mostrar correções específicas se houver
    if [ $CORRECTED -gt 0 ] && [ -s "$CORRECTIONS_LOG" ]; then
        echo -e "  ${YELLOW}📝 Correções realizadas:${RESET}"
        echo ""
        while IFS= read -r line; do
            echo -e "  ${DIM}•${RESET} $line"
        done < "$CORRECTIONS_LOG"
        echo ""
    fi
fi

echo ""
echo -e "  ${DIM}═══════════════════════════════════════════════════════════${RESET}"
echo -e "  ${BOLD}📁 Localizacao:${RESET} $TARGET"

if [ $MOVED -gt 0 ]; then
    CAT_COUNT=$(find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" | wc -l)
    echo -e "  ${BOLD}📂 Categorias utilizadas:${RESET} $CAT_COUNT"
fi

if [ $EMPTY_REMOVED -gt 0 ]; then
    echo -e "  ${GREEN}🗑 Pastas vazias removidas:${RESET} $EMPTY_REMOVED"
fi

echo ""
echo -e "  ${BOLD}💡 Dica:${RESET} Execute novamente para verificar/corrigir novos arquivos"
echo -e "  ${DIM}O script é seguro para execuções múltiplas!${RESET}"
echo ""

# Listar pastas de categorias existentes (opcional)
if [ $MOVED -gt 0 ] || [ -n "$(find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" 2>/dev/null)" ]; then
    echo -e "  ${DIM}Pastas de categorias atuais:${RESET}"
    find "$TARGET" -maxdepth 1 -type d ! -path "$TARGET" 2>/dev/null | sed 's|.*/|    • |' | sort
    echo ""
fi

echo -e "  ${GREEN}✨ Pronto! Sistema organizado e mantido!${RESET}"
echo ""
