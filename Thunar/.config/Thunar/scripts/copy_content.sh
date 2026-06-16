#!/bin/bash
# Copia conteúdo de arquivo para área de transferência
# Uso: copy_content.sh <arquivo>

ARQUIVO="$1"
NOME=$(basename "$ARQUIVO")

erro() { notify-send "Falha ao copiar" "$1" -i error; exit 1; }

[ -z "$ARQUIVO" ]   && erro "Nenhum arquivo selecionado"
[ ! -f "$ARQUIVO" ] && erro "Arquivo não encontrado: $NOME"

if   command -v xclip   &>/dev/null; then xclip -selection clipboard < "$ARQUIVO"
elif command -v xsel    &>/dev/null; then xsel --clipboard --input    < "$ARQUIVO"
elif command -v wl-copy &>/dev/null; then wl-copy                     < "$ARQUIVO"
else erro "Instale xclip, xsel ou wl-copy"
fi

[ $? -eq 0 ] && notify-send "Conteúdo copiado" "$NOME" -i info \
             || erro "Erro ao copiar para clipboard"
