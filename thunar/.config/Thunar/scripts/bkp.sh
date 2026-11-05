#!/usr/bin/env bash
for file in "$@"; do
    dir=$(dirname "$file")
    filename=$(basename "$file")
    ts=$(date +%d-%m-%Y_%H-%M-%S-%3N)

    # Trata dotfiles, arquivos sem extensão e com extensão
    if [[ "$filename" == .* ]]; then
        new_name="${dir}/${filename}_${ts}"
    else
        base="${filename%.*}"
        ext="${filename##*.}"
        if [ "$base" = "$filename" ]; then
            new_name="${dir}/${base}_${ts}"
        else
            new_name="${dir}/${base}_${ts}.${ext}"
        fi
    fi

    cp -r "$file" "$new_name" || notify-send "Thunar: erro ao copiar" "$filename"
done
