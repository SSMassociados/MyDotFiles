#!/bin/bash
# Gera um arquivo compatível com o i3 a partir das cores do pywal.

# Caminhos
wal_colors="$HOME/.cache/wal/colors"
i3_colors="$HOME/.cache/wal/colors_i3"

# Gera o arquivo para i3
echo "# Gerado por generate_colors_i3.sh" > "$i3_colors"

# Adiciona as cores no formato esperado
for i in {0..15}; do
  color=$(sed -n "$((i+1))p" "$wal_colors") # Lê cada linha de 'colors'
  echo "set_from_resource \$color$i color$i \"$color\"" >> "$i3_colors"
done
