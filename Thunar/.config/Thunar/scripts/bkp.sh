veja esse script: #!/usr/bin/env bash

# Itera sobre todos os arquivos selecionados no Thunar
for file in "$@"; do
    # Obtém o diretório, nome completo, base e extensão
    dir=$(dirname "$file")
    filename=$(basename "$file")
    base="${filename%.*}"
    ext="${filename##*.}"
    
    # Gera o timestamp no formato Dia-Mes-Ano_Hora-Min-Seg
    ts=$(date +%d-%m-%Y_%H-%M-%S)
    
    # Verifica se o arquivo tem extensão ou se é um diretório
    if [ "$base" = "$filename" ]; then
        new_name="${dir}/${base}_${ts}"
    else
        new_name="${dir}/${base}_${ts}.${ext}"
    fi
    
    # Copia (suporta pastas com -r)
    cp -r "$file" "$new_name"
done
