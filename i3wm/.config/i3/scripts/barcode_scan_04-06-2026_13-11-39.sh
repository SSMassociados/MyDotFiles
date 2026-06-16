#!/usr/bin/env bash
# barcode_scan.sh
# Dependências: flameshot zbar imagemagick xclip libnotify
# Opcionais: tesseract java (ZXing)
# Arch: yay -S flameshot zbar imagemagick xclip libnotify tesseract

set -u

ZXING_DIR="$HOME/.local/bin/zxing"
ZXING_JAR="$ZXING_DIR/zxing.jar"
ZXING_CORE="$ZXING_DIR/core.jar"

# Compatibilidade ImageMagick v6/v7
if command -v magick >/dev/null 2>&1; then
    MAGICK_CMD="magick"
else
    MAGICK_CMD="convert"
fi

check_dependencies() {
    local required=("flameshot" "zbarimg" "xclip" "notify-send")
    local missing=()

    for dep in "${required[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done

    if ! command -v magick >/dev/null 2>&1 &&
       ! command -v convert >/dev/null 2>&1; then
        missing+=("imagemagick")
    fi

    if (( ${#missing[@]} > 0 )); then
        echo "Erro: Dependências faltando:"
        printf ' - %s\n' "${missing[@]}"
        echo
        echo "Instale com:"
        echo "yay -S flameshot zbar imagemagick xclip libnotify"
        exit 1
    fi
}

install_zxing() {

    command -v java >/dev/null 2>&1 || return 0

    if [[ -f "$ZXING_JAR" && -f "$ZXING_CORE" ]]; then
        return 0
    fi

    echo "ZXing não encontrado. Baixando..."

    mkdir -p "$ZXING_DIR"

    wget -q \
        "https://repo1.maven.org/maven2/com/google/zxing/javase/3.5.1/javase-3.5.1.jar" \
        -O "$ZXING_JAR" || return 1

    wget -q \
        "https://repo1.maven.org/maven2/com/google/zxing/core/3.5.1/core-3.5.1.jar" \
        -O "$ZXING_CORE" || return 1
}

zxing_read() {

    local image="$1"

    [[ -f "$ZXING_JAR" ]] || return 1
    [[ -f "$ZXING_CORE" ]] || return 1

    java \
        -cp "$ZXING_JAR:$ZXING_CORE" \
        com.google.zxing.client.j2se.CommandLineRunner \
        "$image" 2>/dev/null |
        grep -oP 'content:\K.*'
}

cleanup() {
    rm -f "$temp_img" "$temp_processed"
}

scan_barcode() {

    local barcode_result=""
    local ocr_result=""

    temp_img=$(mktemp /tmp/barcode_scan.XXXXXX.png)
    temp_processed=$(mktemp /tmp/barcode_processed.XXXXXX.png)

    trap cleanup EXIT

    flameshot gui -r > "$temp_img"

    if [[ ! -s "$temp_img" ]]; then
        echo "Captura cancelada."
        exit 0
    fi

    # Pré-processamento
    "$MAGICK_CMD" "$temp_img" \
        -colorspace Gray \
        -auto-level \
        -sharpen 0x1 \
        -resize 300% \
        "$temp_processed"

    # ==================================================
    # Tentativa 1: ZBar imagem original
    # ==================================================
    barcode_result=$(zbarimg -q --raw "$temp_img" 2>/dev/null)

    # ==================================================
    # Tentativa 2: ZBar imagem processada
    # ==================================================
    if [[ -z "$barcode_result" ]]; then
        barcode_result=$(zbarimg -q --raw "$temp_processed" 2>/dev/null)
    fi

    # ==================================================
    # Tentativa 3: ZXing
    # ==================================================
    if [[ -z "$barcode_result" ]] && command -v java >/dev/null 2>&1; then

        barcode_result=$(zxing_read "$temp_img")

        if [[ -z "$barcode_result" ]]; then
            barcode_result=$(zxing_read "$temp_processed")
        fi
    fi

    # ==================================================
    # Tentativa 4: OCR (último recurso)
    # ==================================================
    if [[ -z "$barcode_result" ]] &&
       command -v tesseract >/dev/null 2>&1; then

        ocr_result=$(
            LANG=pt_BR.UTF-8 \
            tesseract "$temp_processed" stdout 2>/dev/null |
            tr -dc '0-9A-Za-z'
        )

        # Evita falsos positivos muito curtos
        if [[ ${#ocr_result} -ge 6 ]]; then
            barcode_result="$ocr_result"
            echo "⚠️ Lido via OCR (resultado pode ser impreciso)"
        fi
    fi

    # ==================================================
    # Resultado
    # ==================================================
    if [[ -n "$barcode_result" ]]; then

        printf '%s' "$barcode_result" | \
            xclip -selection clipboard

        notify-send \
            "Leitor de Código" \
            "Código: $barcode_result" \
            -u normal

        echo "✅ Código detectado:"
        echo "$barcode_result"
        echo
        echo "📋 Copiado para a área de transferência"

    else

        notify-send \
            "Leitor de Código" \
            "Nenhum código detectado" \
            -u critical

        echo "❌ Nenhum código detectado."
        echo "Tente selecionar uma área mais próxima do código."
    fi
}

check_dependencies
install_zxing
scan_barcode
