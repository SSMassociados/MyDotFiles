#!/bin/bash

# Verifica se o pdftotext está instalado
if ! [ -x "$(command -v pdftotext)" ]; then
  echo 'Erro: pdftotext não está instalado. Por favor, instale-o antes de executar este script.' >&2
  exit 1
fi

# Verifica se o pacote dunstify está instalado para notificações visuais
if ! [ -x "$(command -v dunstify)" ]; then
  echo 'Erro: dunstify não está instalado. Por favor, instale-o antes de executar este script.' >&2
  exit 1
fi

# Verifica se o pacote pulseaudio-utils está instalado para reprodução de áudio
if ! [ -x "$(command -v paplay)" ]; then
  echo 'Erro: pulseaudio-utils não está instalado. Por favor, instale-o antes de executar este script.' >&2
  exit 1
fi

# Verifica se foram fornecidos argumentos de linha de comando
if [ $# -eq 0 ]; then
  echo "Erro: Forneça os nomes dos arquivos PDF a serem convertidos como argumentos." >&2
  echo "Exemplo: $0 arquivo1.pdf arquivo2.pdf" >&2
  exit 1
fi

# Cria uma subpasta chamada "TXT_Output" no diretório atual se não existir
mkdir -p "TXT_Output"

# Loop através de cada arquivo PDF fornecido como argumento
for file in "$@"; do
    # Verifica se o arquivo PDF existe
    if [ -f "$file" ]; then
        # Extrai o nome do arquivo sem extensão
        filename=$(basename -- "$file")
        filename_no_ext="${filename%.pdf}"

        # Substitui "-" por "_"
        filename_no_ext="${filename_no_ext//-/_}"

        # Define o nome do arquivo de saída com a extensão .txt
        output_file="$filename_no_ext.txt"

        # Converte o arquivo PDF em um arquivo de texto mantendo o layout
        pdftotext -layout "$file" "TXT_Output/$output_file"
        
        # Exibe uma notificação visual para cada arquivo convertido
        dunstify -u normal -t 3000 "PDF to TXT Conversion" "Conversão do arquivo $file concluída."
                
        # Toca uma notificação sonora após a conversão de cada arquivo
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga
    else
        echo "Aviso: O arquivo $file não foi encontrado e será ignorado."
    fi
done
