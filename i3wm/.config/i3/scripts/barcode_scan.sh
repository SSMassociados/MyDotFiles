#!/bin/bash

# Script de leitura de código de barras com zbarimg, fallback com ZXing e OCR
# Requer: flameshot, zbarimg, imagemagick, xclip, (opcional: tesseract, java + zxing)

check_dependencies() {
    dependencies=("flameshot" "zbarimg" "xclip" "convert" "java")
    missing=()
    
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo "Erro: Dependências faltando: ${missing[*]}"
        echo "Instale com: sudo pacman -S flameshot zbar xclip imagemagick tesseract jre-openjdk"
        exit 1
    fi

    if [ ! -f ~/.local/bin/zxing/zxing.jar ]; then
        echo "ZXing não encontrado. Instalando em ~/.local/bin/zxing ..."
        mkdir -p ~/.local/bin/zxing
        wget -q https://repo1.maven.org/maven2/com/google/zxing/javase/3.5.1/javase-3.5.1.jar \
             -O ~/.local/bin/zxing/zxing.jar || {
            echo "Falha ao baixar ZXing"
            exit 1
        }
    fi
}

zxing_read() {
    local image="$1"
    java -cp ~/.local/bin/zxing/zxing.jar com.google.zxing.client.j2se.CommandLineRunner "$image" \
        2>/dev/null | grep -oP 'content:\K.*'
}

cleanup() {
    rm -f "$temp_img" "$temp_processed"
}
trap cleanup EXIT

scan_barcode() {
    temp_img=$(mktemp /tmp/barcode_scan.XXXXXX.png)
    temp_processed=$(mktemp /tmp/barcode_processed.XXXXXX.png)

    flameshot gui -r > "$temp_img"

    if [ ! -s "$temp_img" ]; then
        echo "Captura cancelada."
        exit 0
    fi

    convert "$temp_img" \
        -resize 300% \
        -colorspace Gray \
        -auto-level \
        -contrast-stretch 10% \
        -sharpen 0x2 \
        "$temp_processed"

    barcode_result=$(zbarimg -q --raw "$temp_processed" 2>/dev/null)

    # ZXing como fallback
    if [ -z "$barcode_result" ]; then
        barcode_result=$(zxing_read "$temp_processed")
    fi

    # OCR como último recurso
    if [ -z "$barcode_result" ] && command -v tesseract &>/dev/null; then
        ocr_result=$(tesseract "$temp_processed" stdout 2>/dev/null | tr -dc '0-9')
        if [ -n "$ocr_result" ]; then
            barcode_result="$ocr_result"
            echo "⚠️ Lido via OCR (tesseract): $barcode_result"
        fi
    fi

    if [ -n "$barcode_result" ]; then
        echo -n "$barcode_result" | xclip -selection clipboard
        notify-send "Leitor de Código" "Código: $barcode_result" -u normal
        echo "✅ Código detectado: $barcode_result (copiado para clipboard)"
    else
        notify-send "Leitor de Código" "Nenhum código detectado" -u critical
        echo "❌ Nenhum código detectado. Tente ajustar zoom, luz ou ângulo."
    fi
}

check_dependencies
scan_barcode
