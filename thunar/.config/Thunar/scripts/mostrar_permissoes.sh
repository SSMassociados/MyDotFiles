#!/bin/bash
# Script: mostrar_permissoes.sh
# Mostra permissões simbólicas, numéricas, dono e grupo de forma compacta

arquivo="$1"
nome=$(basename "$arquivo")  # Apenas o nome, sem caminho

# Captura permissões simbólicas e numéricas
permissoes=$(stat -c "%A %a" "$arquivo")
dono=$(stat -c "%U" "$arquivo")
grupo=$(stat -c "%G" "$arquivo")

# Texto a ser exibido
texto="Arquivo: $nome
Permissões: $permissoes
Dono: $dono
Grupo: $grupo"

# Exibe na janela GTK3 com Zenity de forma compacta
zenity --info \
  --title="Informações do Arquivo" \
  --text="$texto" \
  --no-wrap
