#!/bin/bash

# Definir o tema do GTK
export GTK_THEME=Adwaita:light

# Encontrar o nome da impressora padrão
printer_name=$(lpstat -d | awk '{print $5}')

# Verificar se o nome da impressora padrão foi encontrado
if [ -z "$printer_name" ]; then
    echo "Não foi possível encontrar a impressora padrão."
    exit 1
fi

# Abrir a fila da impressora
system-config-printer -p "$printer_name"
